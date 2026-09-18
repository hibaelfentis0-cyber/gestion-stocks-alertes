import pandas as pd
import streamlit as st

# Charger les 4 fichiers de stock
df_prod = pd.read_excel("01_Production_Stock_Alert.xlsx")
df_log = pd.read_excel("02_Logistics_Stock_Alert.xlsx")
df_purch = pd.read_excel("03_Purchasing_Supply_Stock_Alert.xlsx")
df_trans = pd.read_excel("04_Transport_Delivery_Stock_Alert.xlsx")
