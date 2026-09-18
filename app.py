import pandas as pd
import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="Supply Chain Control", page_icon="📦", layout="wide"
)

# Chargement des 4 fichiers Excel avec header=3 pour éviter les lignes vides
@st.cache_data
def load_data():
  df_prod = pd.read_excel("01_Production_Stock_Alert.xlsx", header=3)
  df_log = pd.read_excel("02_Logistics_Stock_Alert.xlsx", header=3)
  df_purch = pd.read_excel("03_Purchasing_Supply_Stock_Alert.xlsx", header=3)
  df_trans = pd.read_excel("04_Transport_Delivery_Stock_Alert.xlsx", header=3)
  return df_prod, df_log, df_purch, df_trans


df_prod, df_log, df_purch, df_trans = load_data()

# ==================== NAVIGATION (MENU LATÉRAL) ====================
st.sidebar.title("🛠️ Supply Chain Menu")
menu = st.sidebar.radio(
    "Aller à",
    [
        "📊 Dashboard Total",
        "🏭 Production",
        "📦 Logistique",
        "🛒 Approvisionnement",
        "🚚 Transport",
    ],
)

# ==================== 1. DASHBOARD TOTAL ====================
if menu == "📊 Dashboard Total":
  st.title("📊 Tableau de Bord Global - Supply Chain")
  st.write(
      "Vue d'ensemble et indicateurs clés de performance (KPI) pour tous les"
      " départements."
  )

  # Affichage des KPIs en haut (chiffres globaux)
  col1, col2, col3, col4 = st.columns(4)
  with col1:
    st.metric(
        label="Alertes Production", value=len(df_prod), delta="-2 vs hier"
    )
  with col2:
    st.metric(label="Articles Logistique", value=len(df_log), delta="Stable")
  with col3:
    st.metric(
        label="Commandes Achats", value=len(df_purch), delta="+3 en attente"
    )
  with col4:
    st.metric(label="Livraisons Transport", value=len(df_trans), delta="1 retard")

  st.divider()

  # Graphiques simples et visuels
  st.subheader("📈 Répartition des Alertes par Département")
  # Création d'un petit graphique en barres simple basé sur le nombre de lignes
  chart_data = pd.DataFrame({
      "Département": ["Production", "Logistique", "Approvisionnement", "Transport"],
      "Nombre d'éléments": [
          len(df_prod),
          len(df_log),
          len(df_purch),
          len(df_trans),
      ],
  })
  st.bar_chart(chart_data.set_index("Département"))

# ==================== 2. PRODUCTION ====================
elif menu == "🏭 Production":
  st.title("🏭 Suivi - Production Stock Alert")
  st.write(
      "Gestion et suivi des alertes de stock critique émanant de la production."
  )
  st.dataframe(df_prod, use_container_width=True)

# ==================== 3. LOGISTIQUE ====================
elif menu == "📦 Logistique":
  st.title("📦 Suivi - Logistique & Entrepôt")
  st.write("État des stocks en entrepôt, emplacements et suivi des palettes.")
  st.dataframe(df_log, use_container_width=True)

# ==================== 4. APPROVISIONNEMENT ====================
elif menu == "🛒 Approvisionnement":
  st.title("🛒 Suivi - Approvisionnement & Achats")
  st.write("Gestion des ruptures, calculs automatiques et bons de commande.")
  st.dataframe(df_purch, use_container_width=True)

# ==================== 5. TRANSPORT ====================
elif menu == "🚚 Transport":
  st.title("🚚 Suivi - Transport & Livraison")
  st.write("Suivi des expéditions, des transporteurs et des retards éventuels.")
  st.dataframe(df_trans, use_container_width=True)
elif menu == "Historique":
  st.title("📜 Historique des Alertes")
  st.write("Consultez l'historique complet des mouvements et des résolutions.")
