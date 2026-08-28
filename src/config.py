"""
Connexion a MongoDB Atlas.

Les identifiants sont lus depuis le fichier .env (jamais en dur dans le code).
C'est le seul endroit du projet qui ouvre une connexion : tous les autres
modules importent get_db() depuis ici.
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "dvf")
COLL_MUTATIONS = os.getenv("COLL_MUTATIONS", "mutations")
COLL_COMMUNES = os.getenv("COLL_COMMUNES", "communes")


def get_client() -> MongoClient:
    """Ouvre une connexion Atlas et verifie qu'elle repond avant de la rendre."""
    if not MONGODB_URI:
        raise ConfigurationError(
            "MONGODB_URI absent. Copiez .env.example en .env et remplissez-le."
        )
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=8000)
    try:
        client.admin.command("ping")
    except ConnectionFailure as e:
        raise ConnectionFailure(
            f"Impossible de joindre Atlas. Verifiez l'URI et l'acces reseau (IP autorisee). Detail : {e}"
        )
    return client


def get_db():
    """Renvoie l'objet base de donnees pret a l'emploi."""
    return get_client()[DB_NAME]


if __name__ == "__main__":
    db = get_db()
    print(f"Connexion OK -> base '{db.name}'")
    print("Collections presentes :", db.list_collection_names())
