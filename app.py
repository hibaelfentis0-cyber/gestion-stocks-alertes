import pandas as pd
import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="Supply Chain Control - Alertes", page_icon="📊", layout="wide"
)

# Sidebar (Menu sur le côté comme sur ton image)
st.sidebar.title("Navigation")
menu = st.sidebar.radio(
    "Aller à", ["Tableau de Bord", "Nouvelle Alerte", "Historique"]
)

# Chargement des 4 fichiers Excel avec header=3 pour éviter les lignes vides
df_prod = pd.read_excel("01_Production_Stock_Alert.xlsx", header=3)
df_log = pd.read_excel("02_Logistics_Stock_Alert.xlsx", header=3)
df_purch = pd.read_excel("03_Purchasing_Supply_Stock_Alert.xlsx", header=3)
df_trans = pd.read_excel("04_Transport_Delivery_Stock_Alert.xlsx", header=3)

# Logique d'affichage selon le choix du menu
if menu == "Tableau de Bord":
  st.title("📊 Supply Chain Control - Tableau de Bord des Alertes")

  tab1, tab2, tab3, tab4 = st.tabs(
      ["Production", "Logistique", "Achats", "Transport"]
  )

  with tab1:
    st.subheader("1. Production Stock Alert")
    st.dataframe(df_prod, use_container_width=True)

  with tab2:
    st.subheader("2. Logistics Processing")
    st.dataframe(df_log, use_container_width=True)

  with tab3:
    st.subheader("3. Purchasing & Supply")
    st.dataframe(df_purch, use_container_width=True)

  with tab4:
    st.subheader("4. Transport & Delivery")
    st.dataframe(df_trans, use_container_width=True)

elif menu == "Nouvelle Alerte":
  st.title("➕ Créer une Nouvelle Alerte")
  st.write(
      "Formulaire de saisie pour ajouter une nouvelle alerte de stock dans le"
      " système."
  )
  # Tu pourras ajouter des champs de saisie ici si tu veux

elif menu == "Historique":
  st.title("📜 Historique des Alertes")
  st.write("Consultez l'historique complet des mouvements et des résolutions.")
