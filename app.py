import pandas as pd
import streamlit as st

st.title("📦 Tableau de bord - Gestion des Alertes de Stock")

# Charger les 4 fichiers de stock
df_prod = pd.read_excel("01_Production_Stock_Alert.xlsx")
df_log = pd.read_excel("02_Logistics_Stock_Alert.xlsx")
df_purch = pd.read_excel("03_Purchasing_Supply_Stock_Alert.xlsx")
df_trans = pd.read_excel("04_Transport_Delivery_Stock_Alert.xlsx")

# Afficher chaque tableau dans l'application
st.subheader("1. Production Stock Alert")
st.dataframe(df_prod)

st.subheader("2. Logistics Processing")
st.dataframe(df_log)

st.subheader("3. Purchasing & Supply")
st.dataframe(df_purch)

st.subheader("4. Transport & Delivery")
st.dataframe(df_trans)
