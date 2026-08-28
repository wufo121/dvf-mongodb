"""
Chargement du DVF geolocalise (format officiel files.data.gouv.fr/geo-dvf)
vers MongoDB Atlas.

Transformation cle du projet :
  le CSV source a UNE LIGNE PAR LOT/PARCELLE. On regroupe ces lignes par
  id_mutation pour construire UN document 'mutation' avec ses lots EMBARQUES.
  -> decision d'architecture principale, materialisee ici.

En parallele : collection 'communes' (referentiel, referencee par code INSEE).

Filtrage au chargement (argument M0) : on ne garde que certains departements,
car la France entiere (1,3 M mutations) ne tient pas sur un cluster gratuit.

Usage :
    python -m src.load_data --csv data/full.csv.gz --departements 75 92 93
    python -m src.load_data --csv data/full.csv.gz --departements 92 --limit 20000
"""
import argparse
import csv
import gzip
from datetime import datetime

from src.config import get_db, COLL_MUTATIONS, COLL_COMMUNES

# Les 5 paires de colonnes lotN_numero / lotN_surface_carrez du format officiel
LOT_COLS = [(f"lot{i}_numero", f"lot{i}_surface_carrez") for i in range(1, 6)]


def ouvrir(path):
    """Ouvre un CSV, gzip ou non, de facon transparente."""
    if path.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", newline="")
    return open(path, "rt", encoding="utf-8", newline="")


def to_float(x):
    if x is None or x == "":
        return None
    try:
        return float(x)
    except ValueError:
        return None


def to_int(x):
    v = to_float(x)
    return int(v) if v is not None else None


def build_mutation(mut_id, lignes):
    """Construit un document mutation a partir de toutes ses lignes source."""
    p = lignes[0]

    lon = to_float(p.get("longitude"))
    lat = to_float(p.get("latitude"))
    localisation = None
    if lon is not None and lat is not None:
        localisation = {"type": "Point", "coordinates": [lon, lat]}

    date_mut = None
    if p.get("date_mutation"):
        try:
            date_mut = datetime.fromisoformat(p["date_mutation"])
        except ValueError:
            date_mut = None

    # Lots embarques : chaque ligne source devient un lot.
    # On y met le bati, le local, et les eventuels lots carrez de la ligne.
    lots = []
    for l in lignes:
        surfaces_carrez = []
        for _, col_surf in LOT_COLS:
            s = to_float(l.get(col_surf))
            if s:
                surfaces_carrez.append(s)
        lots.append({
            "type_local": l.get("type_local") or None,
            "surface_bati": to_float(l.get("surface_reelle_bati")),
            "nb_pieces": to_int(l.get("nombre_pieces_principales")),
            "surface_terrain": to_float(l.get("surface_terrain")),
            "nature_culture": l.get("nature_culture") or None,
            "surfaces_carrez": surfaces_carrez,
        })

    return {
        "_id": mut_id,
        "date_mutation": date_mut,
        "nature_mutation": p.get("nature_mutation") or None,
        "valeur_fonciere": to_float(p.get("valeur_fonciere")),
        "code_commune": p.get("code_commune") or None,
        "nom_commune": p.get("nom_commune") or None,        # denormalisation assumee
        "code_postal": p.get("code_postal") or None,
        "code_departement": p.get("code_departement") or None,
        "adresse": " ".join(x for x in [
            p.get("adresse_numero"), p.get("adresse_nom_voie")] if x) or None,
        "localisation": localisation,
        "nb_lots": len(lots),
        "lots": lots,
    }


def charger(csv_path, departements=None, limit=None, batch_size=1000):
    db = get_db()
    mutations = db[COLL_MUTATIONS]
    communes = db[COLL_COMMUNES]
    mutations.drop()
    communes.drop()

    dept_set = set(departements) if departements else None
    communes_vues = {}
    batch = []
    courant_id = None
    courant_lignes = []
    n = 0

    def flush(b):
        if b:
            mutations.insert_many(b, ordered=False)

    with ouvrir(csv_path) as f:
        reader = csv.DictReader(f)
        for ligne in reader:
            if dept_set and ligne.get("code_departement") not in dept_set:
                continue

            mid = ligne.get("id_mutation")
            if mid != courant_id:
                if courant_lignes:
                    batch.append(build_mutation(courant_id, courant_lignes))
                    n += 1
                    if len(batch) >= batch_size:
                        flush(batch); batch = []
                    if limit and n >= limit:
                        courant_lignes = []; break
                courant_id = mid
                courant_lignes = []

            courant_lignes.append(ligne)

            code_c = ligne.get("code_commune")
            if code_c and code_c not in communes_vues:
                communes_vues[code_c] = {
                    "_id": code_c,
                    "nom": ligne.get("nom_commune") or None,
                    "code_postal": ligne.get("code_postal") or None,
                    "code_departement": ligne.get("code_departement") or None,
                }

        if courant_lignes and (not limit or n < limit):
            batch.append(build_mutation(courant_id, courant_lignes)); n += 1

    flush(batch)
    if communes_vues:
        communes.insert_many(list(communes_vues.values()), ordered=False)

    print(f"Charge : {n} mutations, {len(communes_vues)} communes.")
    return n


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--departements", nargs="*", default=None,
                    help="ex: 75 92 93 (vide = tout, deconseille sur M0)")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    charger(args.csv, departements=args.departements, limit=args.limit)
