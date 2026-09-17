import streamlit as st
import pandas as pd

st.set_page_config(page_title="Supply Chain Control", layout="wide")

st.title("Supply Chain Control : Gestion des Alertes de Stock")

@st.cache_data
def load_data():
    try:
        return pd.read_excel("Production1_Alerts_Dashboard.xlsx")
    except Exception as e:
        return None

df = load_data()

if df is None:
    st.error("⚠️ Fichier Excel introuvable ou illisible.")
else:
    st.sidebar.title("Navigation")
    menu = st.sidebar.radio("Aller à", ["Tableau de Bord", "Nouvelle Alerte", "Historique"])

    if menu == "Tableau de Bord":
        st.subheader("📊 Tableau de Bord Global")
        st.dataframe(df, use_container_width=True)
        st.metric("Total Articles", len(df))

    elif menu == "Nouvelle Alerte":
        st.subheader("🚨 Déclarer une Alerte")
        st.success("Formulaire prêt.")

    elif menu == "Historique":
        st.subheader("📁 Historique")
        st.dataframe(df, use_container_width=True)
