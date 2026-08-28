"""
Genere un CSV synthetique au format EXACT du DVF geolocalise
(files.data.gouv.fr/geo-dvf), pour tester le pipeline sans le vrai fichier.

Il reproduit volontairement les defauts du vrai jeu :
  - une meme vente (id_mutation) eclatee sur plusieurs lignes = un lot par ligne
  - des valeur_fonciere vides
  - des latitude/longitude manquantes
  - des surfaces a zero

Usage :
    python scripts/generate_sample.py --n 15000 --out data/sample_dvf.csv
"""
import argparse
import csv
import random
from datetime import date, timedelta

# Colonnes reelles d'un fichier geo-dvf (sous-ensemble suffisant pour le projet)
COLUMNS = [
    "id_mutation", "date_mutation", "nature_mutation", "valeur_fonciere",
    "code_postal", "code_commune", "nom_commune", "code_departement",
    "id_parcelle", "lot1_numero", "lot1_surface_carrez", "nombre_lots",
    "type_local", "surface_reelle_bati", "nombre_pieces_principales",
    "surface_terrain", "longitude", "latitude",
]

COMMUNES = [
    # (code_commune, nom, code_postal, dept, lon, lat)
    ("92050", "Nanterre", "92000", "92", 2.206, 48.892),
    ("92026", "Courbevoie", "92400", "92", 2.256, 48.897),
    ("92044", "Levallois-Perret", "92300", "92", 2.287, 48.895),
    ("75056", "Paris", "75015", "75", 2.300, 48.842),
    ("93066", "Saint-Denis", "93200", "93", 2.358, 48.936),
    ("93048", "Montreuil", "93100", "93", 2.441, 48.861),
    ("92063", "Sevres", "92310", "92", 2.211, 48.823),
]
TYPES = ["Appartement", "Maison", "Local industriel. commercial ou assimile", "Dependance"]


def rand_date(rng):
    start = date(2020, 1, 1)
    return (start + timedelta(days=rng.randint(0, 5 * 365))).isoformat()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=15000, help="nombre de mutations")
    ap.add_argument("--out", default="data/sample_dvf.csv")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    import os
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    rows = []
    for i in range(args.n):
        mut_id = f"2023-{i:06d}"
        commune = rng.choice(COMMUNES)
        code_c, nom_c, cp, dept, lon, lat = commune
        d = rand_date(rng)
        nature = "Vente"

        # 92% des ventes ont 1 a 4 lots, une minorite en a beaucoup (copropriete)
        if rng.random() < 0.92:
            nb_lots = rng.randint(1, 4)
        else:
            nb_lots = rng.randint(6, 250)  # les grosses ventes qui testent l'embarquement

        # valeur fonciere : parfois vide (donnee sale)
        if rng.random() < 0.05:
            valeur = ""
        else:
            valeur = str(rng.randint(80_000, 1_200_000))

        # coordonnees : parfois absentes (donnee sale)
        if rng.random() < 0.08:
            lon_v, lat_v = "", ""
        else:
            lon_v = f"{lon + rng.uniform(-0.02, 0.02):.6f}"
            lat_v = f"{lat + rng.uniform(-0.02, 0.02):.6f}"

        # une ligne CSV par lot (c'est ainsi que le vrai DVF est structure)
        for lot_idx in range(1, nb_lots + 1):
            type_local = rng.choice(TYPES)
            surface = rng.randint(15, 180) if rng.random() > 0.03 else 0  # parfois 0
            rows.append({
                "id_mutation": mut_id,
                "date_mutation": d,
                "nature_mutation": nature,
                "valeur_fonciere": valeur,
                "code_postal": cp,
                "code_commune": code_c,
                "nom_commune": nom_c,
                "code_departement": dept,
                "id_parcelle": f"{code_c}000AB{rng.randint(1000,9999)}",
                "lot1_numero": str(lot_idx),
                "lot1_surface_carrez": f"{surface}.0" if surface else "",
                "nombre_lots": str(nb_lots),
                "type_local": type_local,
                "surface_reelle_bati": str(surface),
                "nombre_pieces_principales": str(rng.randint(1, 6)),
                "surface_terrain": str(rng.randint(0, 400)),
                "longitude": lon_v,
                "latitude": lat_v,
            })

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)

    print(f"{args.n} mutations -> {len(rows)} lignes ecrites dans {args.out}")


if __name__ == "__main__":
    main()
