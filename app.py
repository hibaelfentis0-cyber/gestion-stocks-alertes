import pandas as pd
import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="Supply Chain Control Center", page_icon="📦", layout="wide"
)

# Chargement des 4 fichiers Excel avec le bon décalage (header=3)
@st.cache_data
def load_data():
  # On lit à partir de la ligne 4 (index 3) pour capturer les vrais titres des colonnes
  df_prod = pd.read_excel("01_Production_Stock_Alert.xlsx", header=3)
  df_log = pd.read_excel("02_Logistics_Stock_Alert.xlsx", header=3)
  df_purch = pd.read_excel("03_Purchasing_Supply_Stock_Alert.xlsx", header=3)
  df_trans = pd.read_excel("04_Transport_Delivery_Stock_Alert.xlsx", header=3)
  return df_prod, df_log, df_purch, df_trans


df_prod, df_log, df_purch, df_trans = load_data()

# ==================== NAVIGATION (ENGLISH) ====================
st.sidebar.title("🛠️ Supply Chain Menu")
menu = st.sidebar.radio(
    "Navigate to",
    [
        "📊 Global Dashboard",
        "🏭 Production",
        "📦 Logistics",
        "🛒 Purchasing",
        "🚚 Transport",
    ],
)

# ==================== 1. GLOBAL DASHBOARD ====================
if menu == "📊 Global Dashboard":
  st.title("📊 Supply Chain - Global Dashboard")
  st.write(
      "Overview and Key Performance Indicators (KPIs) across all departments."
  )

  # KPIs Metrics
  col1, col2, col3, col4 = st.columns(4)
  with col1:
    st.metric(
        label="Production Alerts", value=len(df_prod), delta="-2 vs yesterday"
    )
  with col2:
    st.metric(label="Logistics Items", value=len(df_log), delta="Stable")
  with col3:
    st.metric(
        label="Purchasing Orders", value=len(df_purch), delta="+3 pending"
    )
  with col4:
    st.metric(
        label="Transport Deliveries", value=len(df_trans), delta="1 delayed"
    )

  st.divider()

  # Simple Chart
  st.subheader("📈 Alerts Distribution by Department")
  chart_data = pd.DataFrame({
      "Department": [
          "Production",
          "Logistics",
          "Purchasing",
          "Transport",
      ],
      "Total Count": [
          len(df_prod),
          len(df_log),
          len(df_purch),
          len(df_trans),
      ],
  })
  st.bar_chart(chart_data.set_index("Department"))

# ==================== 2. PRODUCTION ====================
elif menu == "🏭 Production":
  st.title("🏭 Production Stock Alert Monitoring")
  st.write(
      "Detailed tracking and management of critical stock alerts coming from"
      " production lines."
  )
  st.dataframe(df_prod, use_container_width=True)

# ==================== 3. LOGISTICS ====================
elif menu == "📦 Logistics":
  st.title("📦 Logistics & Warehouse Processing")
  st.write("Warehouse stock levels, bin locations, and pallet management.")
  st.dataframe(df_log, use_container_width=True)

# ==================== 4. PURCHASING ====================
elif menu == "🛒 Purchasing":
  st.title("🛒 Purchasing & Supply Chain")
  st.write("Shortage calculations, purchase orders, and supplier lead times.")
  st.dataframe(df_purch, use_container_width=True)

# ==================== 5. TRANSPORT ====================
elif menu == "🚚 Transport":
  st.title("🚚 Transport & Delivery Tracking")
  st.write("Carrier performance, shipment status, and delivery delay tracking.")
  st.dataframe(df_trans, use_container_width=True)
