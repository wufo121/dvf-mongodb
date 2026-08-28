"""
Rapport analytique par agregations (livrable 5).

Trois agregations, chacune defend une partie de l'architecture :
  1. prix median au m2 par commune et par trimestre   -> exploite le temporel
  2. ecart maison/appartement selon la densite commune -> justifie le REFERENCEMENT
  3. part de volume des ventes multi-lots              -> justifie l'EMBARQUEMENT

Demo : python -m src.aggregations
"""
from src.config import get_db, COLL_MUTATIONS, COLL_COMMUNES


def prix_median_par_commune_trimestre(db, limite=15):
    """Agregation 1 : prix median au m2, par commune et trimestre."""
    coll = db[COLL_MUTATIONS]
    pipeline = [
        {"$match": {
            "valeur_fonciere": {"$gt": 0},
            "date_mutation": {"$ne": None},
            "lots.type_local": "Appartement",
        }},
        {"$addFields": {
            "surface_totale": {"$sum": "$lots.surface_bati"},
        }},
        {"$match": {"surface_totale": {"$gt": 0}}},
        {"$addFields": {
            "prix_m2": {"$divide": ["$valeur_fonciere", "$surface_totale"]},
            "annee": {"$year": "$date_mutation"},
            "trimestre": {"$ceil": {"$divide": [{"$month": "$date_mutation"}, 3]}},
        }},
        {"$group": {
            "_id": {"commune": "$nom_commune", "annee": "$annee", "trimestre": "$trimestre"},
            "prix_m2_median": {"$median": {
                "input": "$prix_m2", "method": "approximate"}},
            "nb_ventes": {"$sum": 1},
        }},
        {"$match": {"nb_ventes": {"$gte": 5}}},
        {"$sort": {"_id.commune": 1, "_id.annee": 1, "_id.trimestre": 1}},
        {"$limit": limite},
    ]
    return list(coll.aggregate(pipeline))


def ecart_maison_appart_par_densite(db):
    """Agregation 2 : ecart de prix m2 maison vs appartement, par taille de commune.
    Utilise $lookup vers 'communes' -> justifie le referencement."""
    coll = db[COLL_MUTATIONS]
    pipeline = [
        {"$match": {"valeur_fonciere": {"$gt": 0}, "lots.surface_bati": {"$gt": 0}}},
        {"$unwind": "$lots"},
        {"$match": {"lots.type_local": {"$in": ["Maison", "Appartement"]},
                    "lots.surface_bati": {"$gt": 0}}},
        {"$addFields": {"prix_m2": {"$divide": ["$valeur_fonciere", "$lots.surface_bati"]}}},
        {"$lookup": {
            "from": COLL_COMMUNES, "localField": "code_commune",
            "foreignField": "_id", "as": "commune_ref"}},
        {"$group": {
            "_id": {"dept": "$code_departement", "type": "$lots.type_local"},
            "prix_m2_moyen": {"$avg": "$prix_m2"},
            "nb": {"$sum": 1},
        }},
        {"$sort": {"_id.dept": 1, "_id.type": 1}},
    ]
    return list(coll.aggregate(pipeline))


def part_volume_multilots(db):
    """Agregation 3 : part du volume (en euros) par tranche de nombre de lots.
    Utilise $size et $facet -> justifie l'embarquement."""
    coll = db[COLL_MUTATIONS]
    pipeline = [
        {"$match": {"valeur_fonciere": {"$gt": 0}, "lots": {"$exists": True, "$ne": []}}},
        {"$addFields": {"nb_lots_calc": {"$size": "$lots"}}},
        {"$facet": {
            "par_tranche": [
                {"$bucket": {
                    "groupBy": "$nb_lots_calc",
                    "boundaries": [1, 2, 6, 21, 100000],
                    "default": "autre",
                    "output": {"nb_mutations": {"$sum": 1},
                               "valeur_totale": {"$sum": "$valeur_fonciere"}},
                }}
            ],
            "total": [
                {"$group": {"_id": None,
                            "valeur_globale": {"$sum": "$valeur_fonciere"},
                            "nb_global": {"$sum": 1}}}
            ],
        }},
        {"$unwind": "$par_tranche"},
        {"$unwind": "$total"},
        {"$project": {
            "tranche": "$par_tranche._id",
            "nb_mutations": "$par_tranche.nb_mutations",
            "valeur_totale": "$par_tranche.valeur_totale",
            "part_volume_pct": {"$multiply": [
                {"$divide": ["$par_tranche.valeur_totale", "$total.valeur_globale"]}, 100]},
        }},
    ]
    return list(coll.aggregate(pipeline))


if __name__ == "__main__":
    db = get_db()
    print("=== 1. Prix median m2 par commune/trimestre (extrait) ===")
    for r in prix_median_par_commune_trimestre(db)[:8]:
        print(r)
    print("\n=== 2. Ecart maison/appartement par departement ===")
    for r in ecart_maison_appart_par_densite(db):
        print(r)
    print("\n=== 3. Part de volume des ventes multi-lots ===")
    for r in part_volume_multilots(db):
        print(r)
