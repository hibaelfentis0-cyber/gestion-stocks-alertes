import pandas as pd
import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="Supply Chain Control Center", page_icon="📦", layout="wide"
)

# Chargement des données avec persistance de session
if "df_prod" not in st.session_state:

  @st.cache_data
  def load_data():
    df_prod = pd.read_excel("01_Production_Stock_Alert.xlsx", header=2)
    df_log = pd.read_excel("02_Logistics_Stock_Alert.xlsx", header=2)
    df_purch = pd.read_excel("03_Purchasing_Supply_Stock_Alert.xlsx", header=2)
    df_trans = pd.read_excel("04_Transport_Delivery_Stock_Alert.xlsx", header=2)
    return df_prod, df_log, df_purch, df_trans

  (
      st.session_state.df_prod,
      st.session_state.df_log,
      st.session_state.df_purch,
      st.session_state.df_trans,
  ) = load_data()

# ==================== NAVIGATION ====================
st.sidebar.title("🛠️ Supply Chain Menu")
menu = st.sidebar.radio(
    "Navigate to",
    [
        "📊 Global Dashboard",
        "🏭 Production",
        "📦 Logistics",
        "🛒 Purchasing",
        "🚚 Transport",
        "➕ Add New Alert",
    ],
)

# ==================== 1. GLOBAL DASHBOARD ====================
if menu == "📊 Global Dashboard":
  st.title("📊 Supply Chain - Global Dashboard")
  st.write(
      "Overview and Key Performance Indicators (KPIs) across all departments."
  )

  col1, col2, col3, col4 = st.columns(4)
  with col1:
    st.metric(
        label="Production Alerts",
        value=len(st.session_state.df_prod),
        delta="-2 vs yesterday",
    )
  with col2:
    st.metric(
        label="Logistics Items",
        value=len(st.session_state.df_log),
        delta="Stable",
    )
  with col3:
    st.metric(
        label="Purchasing Orders",
        value=len(st.session_state.df_purch),
        delta="+3 pending",
    )
  with col4:
    st.metric(
        label="Transport Deliveries",
        value=len(st.session_state.df_trans),
        delta="1 delayed",
    )

  st.divider()

  st.subheader("📈 Alerts Distribution by Department")
  chart_data = pd.DataFrame({
      "Department": [
          "Production",
          "Logistics",
          "Purchasing",
          "Transport",
      ],
      "Total Count": [
          len(st.session_state.df_prod),
          len(st.session_state.df_log),
          len(st.session_state.df_purch),
          len(st.session_state.df_trans),
      ],
  })
  st.bar_chart(chart_data.set_index("Department"))


# Fonction utilitaire pour les départements
def display_department_view(df, title, description):
  st.title(title)
  st.write(description)

  col_f1, col_f2 = st.columns(2)
  filtered_df = df.copy()

  if "Priority" in df.columns:
    priorities = ["All"] + list(df["Priority"].dropna().unique())
    selected_priority = col_f1.selectbox(
        "Filter by Priority", priorities, key=title + "_prio"
    )
    if selected_priority != "All":
      filtered_df = filtered_df[filtered_df["Priority"] == selected_priority]

  if "Alert Status" in df.columns:
    statuses = ["All"] + list(df["Alert Status"].dropna().unique())
    selected_status = col_f2.selectbox(
        "Filter by Status", statuses, key=title + "_status"
    )
    if selected_status != "All":
      filtered_df = filtered_df[filtered_df["Alert Status"] == selected_status]

  st.dataframe(filtered_df, use_container_width=True)

  csv = filtered_df.to_csv(index=False).encode("utf-8")
  st.download_button(
      label="📥 Download filtered data as CSV",
      data=csv,
      file_name=f"{title.replace(' ', '_')}_export.csv",
      mime="text/csv",
  )


# ==================== 2. PRODUCTION ====================
if menu == "🏭 Production":
  display_department_view(
      st.session_state.df_prod,
      "🏭 Production Stock Alert Monitoring",
      "Detailed tracking and management of critical stock alerts.",
  )

# ==================== 3. LOGISTICS ====================
elif menu == "📦 Logistics":
  display_department_view(
      st.session_state.df_log,
      "📦 Logistics & Warehouse Processing",
      "Warehouse stock levels, bin locations, and pallet management.",
  )

# ==================== 4. PURCHASING ====================
elif menu == "🛒 Purchasing":
  display_department_view(
      st.session_state.df_purch,
      "🛒 Purchasing & Supply Chain",
      "Shortage calculations, purchase orders, and supplier lead times.",
  )

# ==================== 5. TRANSPORT ====================
elif menu == "🚚 Transport":
  display_department_view(
      st.session_state.df_trans,
      "🚚 Transport & Delivery Tracking",
      "Carrier performance, shipment status, and delivery delay tracking.",
  )

# ==================== 6. ADD NEW ALERT ====================
elif menu == "➕ Add New Alert":
  st.title("➕ Create a New Alert")
  st.write("Fill out the form below to add a new alert to the system.")

  with st.form("new_alert_form"):
    dept = st.selectbox(
        "Select Department", ["Production", "Logistics", "Purchasing", "Transport"]
    )
    alert_id = st.text_input("Alert ID (e.g., PA-005)")
    product_code = st.text_input("Product Code (e.g., RM-1004)")
    priority = st.selectbox("Priority", ["Critical", "High", "Medium", "Low"])
    status = st.selectbox("Alert Status", ["Open", "In Progress", "Resolved"])
    comments = st.text_area("Comments / Description")

    submitted = st.form_submit_button("Submit Alert")
    if submitted:
      new_row = {
          "Alert ID": alert_id,
          "Product Code": product_code,
          "Priority": priority,
          "Alert Status": status,
          "Comments": comments,
      }
      if dept == "Production":
        st.session_state.df_prod = pd.concat(
            [st.session_state.df_prod, pd.DataFrame([new_row])],
            ignore_index=True,
        )
      elif dept == "Logistics":
        st.session_state.df_log = pd.concat(
            [st.session_state.df_log, pd.DataFrame([new_row])], ignore_index=True
        )
      elif dept == "Purchasing":
        st.session_state.df_purch = pd.concat(
            [st.session_state.df_purch, pd.DataFrame([new_row])],
            ignore_index=True,
        )
      elif dept == "Transport":
        st.session_state.df_trans = pd.concat(
            [st.session_state.df_trans, pd.DataFrame([new_row])],
            ignore_index=True,
        )

      st.success(f"Successfully added new alert to {dept}!")
