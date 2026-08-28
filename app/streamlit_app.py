"""
Interface d'interrogation (bonus, 1 pt).

Permet d'interroger la base sans terminal : filtre par departement et prix,
affiche les ventes sur une carte et les stats agregees.

Lancement : streamlit run app/streamlit_app.py
"""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import get_db, COLL_MUTATIONS  # noqa: E402
from src.aggregations import part_volume_multilots  # noqa: E402

st.set_page_config(page_title="DVF Explorer", layout="wide")
st.title("DVF Explorer — marché immobilier francilien")


@st.cache_resource
def db():
    return get_db()


st.sidebar.header("Filtres")
dept = st.sidebar.selectbox("Département", ["75", "92", "93"])
prix_max = st.sidebar.slider("Prix maximum (€)", 100_000, 2_000_000, 800_000, step=50_000)

filtre = {
    "code_departement": dept,
    "valeur_fonciere": {"$gt": 0, "$lte": prix_max},
    "localisation": {"$ne": None},
}

docs = list(db()[COLL_MUTATIONS].find(filtre).limit(2000))
st.write(f"**{len(docs)} ventes** affichées (limité à 2000 pour la carte)")

if docs:
    points = [{
        "lat": d["localisation"]["coordinates"][1],
        "lon": d["localisation"]["coordinates"][0],
    } for d in docs if d.get("localisation")]
    st.map(pd.DataFrame(points))

    tableau = pd.DataFrame([{
        "commune": d.get("nom_commune"),
        "valeur (€)": d.get("valeur_fonciere"),
        "nb lots": d.get("nb_lots"),
        "adresse": d.get("adresse"),
    } for d in docs])
    st.dataframe(tableau, use_container_width=True)

st.divider()
st.subheader("Répartition du volume par taille de vente")
try:
    part = pd.DataFrame(part_volume_multilots(db()))
    if not part.empty:
        st.bar_chart(part.set_index("tranche")["part_volume_pct"])
except Exception as e:
    st.info(f"Agrégation indisponible : {e}")
