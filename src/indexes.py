"""
Index justifies et mesures (livrable 4).

Pour chaque index : on mesure une requete AVANT creation (COLLSCAN attendu),
on cree l'index, on remesure APRES (IXSCAN attendu). Un index sans sa double
mesure n'est pas compte par l'enonce.

Demo : python -m src.indexes
"""
from pymongo import ASCENDING, DESCENDING, GEOSPHERE, TEXT
from src.config import get_db, COLL_MUTATIONS


def mesurer(coll, filtre, tri=None):
    """Renvoie (stage, docs_examines, ms) pour une requete donnee via explain."""
    curseur = coll.find(filtre)
    if tri:
        curseur = curseur.sort(tri)
    plan = curseur.explain()
    exec_stats = plan["executionStats"]
    stage = plan["queryPlanner"]["winningPlan"]
    while "inputStage" in stage:
        stage = stage["inputStage"]
    return (
        stage.get("stage"),
        exec_stats["totalDocsExamined"],
        exec_stats["executionTimeMillis"],
    )


def demo_index(coll, nom, keys, filtre, tri=None, **kwargs):
    """Cree un index apres l'avoir mesure sans, puis remesure avec."""
    try:
        coll.drop_index(nom)
    except Exception:
        pass

    avant = mesurer(coll, filtre, tri)
    coll.create_index(keys, name=nom, **kwargs)
    apres = mesurer(coll, filtre, tri)

    print(f"\n### Index '{nom}'  ->  requete : {filtre} tri={tri}")
    print(f"  AVANT : stage={avant[0]:10s} docs_examines={avant[1]:>7} temps={avant[2]} ms")
    print(f"  APRES : stage={apres[0]:10s} docs_examines={apres[1]:>7} temps={apres[2]} ms")
    return avant, apres


def creer_tous(db):
    coll = db[COLL_MUTATIONS]

    demo_index(
        coll, "idx_dept_date",
        [("code_departement", ASCENDING), ("date_mutation", DESCENDING)],
        filtre={"code_departement": "92"},
    )

    demo_index(
        coll, "idx_type_surface",
        [("lots.type_local", ASCENDING), ("lots.surface_bati", DESCENDING)],
        filtre={"lots.type_local": "Appartement"},
        tri=[("lots.surface_bati", DESCENDING)],
    )

    demo_index(
        coll, "idx_geo",
        [("localisation", GEOSPHERE)],
        filtre={"localisation": {"$geoWithin": {
            "$centerSphere": [[2.3, 48.86], 2 / 6378.1]}}},
    )


if __name__ == "__main__":
    db = get_db()
    creer_tous(db)
    print("\nIndex presents :", db[COLL_MUTATIONS].index_information().keys())
