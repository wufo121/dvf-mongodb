"""
CRUD sur la collection mutations, avec gestion d'erreurs reelle (livrable 3).

Chaque operation attrape les erreurs PyMongo et renvoie un resultat exploitable
plutot que de laisser remonter une exception brute.

Demo : python -m src.crud
"""
from pymongo.errors import PyMongoError, DuplicateKeyError
from src.config import get_db, COLL_MUTATIONS


def creer_mutation(db, doc):
    """CREATE : insere une mutation. Renvoie l'_id ou None si echec."""
    try:
        res = db[COLL_MUTATIONS].insert_one(doc)
        return res.inserted_id
    except DuplicateKeyError:
        print(f"[creer] _id deja present : {doc.get('_id')}")
        return None
    except PyMongoError as e:
        print(f"[creer] erreur : {e}")
        return None


def lire_mutations(db, filtre=None, limit=10):
    """READ : renvoie une liste de mutations correspondant au filtre."""
    try:
        return list(db[COLL_MUTATIONS].find(filtre or {}).limit(limit))
    except PyMongoError as e:
        print(f"[lire] erreur : {e}")
        return []


def maj_valeur(db, mutation_id, nouvelle_valeur):
    """UPDATE : met a jour la valeur fonciere d'une mutation."""
    try:
        res = db[COLL_MUTATIONS].update_one(
            {"_id": mutation_id},
            {"$set": {"valeur_fonciere": nouvelle_valeur}},
        )
        if res.matched_count == 0:
            print(f"[maj] aucune mutation avec _id={mutation_id}")
        return res.modified_count
    except PyMongoError as e:
        print(f"[maj] erreur : {e}")
        return 0


def supprimer_mutation(db, mutation_id):
    """DELETE : supprime une mutation par son _id."""
    try:
        res = db[COLL_MUTATIONS].delete_one({"_id": mutation_id})
        return res.deleted_count
    except PyMongoError as e:
        print(f"[supprimer] erreur : {e}")
        return 0


if __name__ == "__main__":
    db = get_db()
    demo_id = "_DEMO_CRUD_"

    doc = {"_id": demo_id, "nom_commune": "TestVille", "valeur_fonciere": 100000,
           "code_departement": "92", "nb_lots": 1, "lots": []}
    print("CREATE ->", creer_mutation(db, doc))

    print("READ   ->", lire_mutations(db, {"_id": demo_id}))

    print("UPDATE ->", maj_valeur(db, demo_id, 250000), "document(s) modifie(s)")
    print("READ   ->", lire_mutations(db, {"_id": demo_id}))

    print("DELETE ->", supprimer_mutation(db, demo_id), "document(s) supprime(s)")
