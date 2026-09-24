import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="Stock Alert Management System",
    page_icon="🏢",
    layout="wide"
)

# Custom UI styling
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 8px; border: 1px solid #d1d5db; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    h1, h2, h3 { color: #1e3a8a; }
    </style>
""", unsafe_allow_html=True)

# Initialize Session State for empty database storage across departments
if "production_df" not in st.session_state:
    st.session_state.production_df = pd.DataFrame(columns=["Part / Material", "Required Quantity", "Comment", "Timestamp"])

if "warehouse_df" not in st.session_state:
    st.session_state.warehouse_df = pd.DataFrame(columns=[
        "Part / Material", "Required Quantity", "Available Quantity", 
        "Shortage Quantity", "Stock Status", "Warehouse Location", "Notification", "Comments"
    ])

if "procurement_df" not in st.session_state:
    st.session_state.procurement_df = pd.DataFrame(columns=[
        "Part / Material", "Shortage Quantity", "Supplier", 
        "Purchase Order", "Order Date", "Expected Delivery Date", 
        "Procurement Status", "Comments"
    ])

if "transport_df" not in st.session_state:
    st.session_state.transport_df = pd.DataFrame(columns=[
        "Purchase Order", "Supplier", "Quantity", 
        "Tracking Number", "Shipment Date", "ETA", 
        "Actual Delivery Date", "Transport Status", "Comments"
    ])

# --- SIDEBAR NAVIGATION ---
st.sidebar.markdown("# 🏢 Stock Alert System")
st.sidebar.markdown("### Management Dashboard")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navigation Menu",
    [
        "📈 Dashboard",
        "1. Production",
        "2. Warehouse",
        "3. Procurement",
        "4. Transport"
    ]
)

# Helper function to convert dataframe to excel for download
def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# ==========================================
# 1. DASHBOARD
# ==========================================
if menu == "📈 Dashboard":
    st.title("🏢 Stock Alert Management System — Dashboard")
    st.markdown("""
    **Objective:** Provide a real-time, automated overview of inventory levels, production demands, 
    procurement triggers, and transport tracking across the enterprise supply chain.
    """)
    st.markdown("---")

    prod_count = len(st.session_state.production_df)
    wh_df = st.session_state.warehouse_df
    proc_df = st.session_state.procurement_df
    trans_df = st.session_state.transport_df

    # Global KPI Calculations
    total_alerts = len(wh_df)
    open_alerts = len(wh_df[wh_df["Stock Status"].isin(["Shortage", "Out of Stock", "Critical Stock"])]) if not wh_df.empty else 0
    critical_alerts = len(wh_df[wh_df["Stock Status"].isin(["Critical Stock", "Out of Stock"])]) if not wh_df.empty else 0
    orders_in_progress = len(trans_df[trans_df["Transport Status"].isin(["Ordered", "In Transit"])]) if not trans_df.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📦 Total Alerts", total_alerts)
    with col2:
        st.metric("⚠️ Open Alerts", open_alerts)
    with col3:
        st.metric("🚨 Critical Alerts", critical_alerts)
    with col4:
        st.metric("🚚 Orders in Progress", orders_in_progress)

    st.markdown("---")
    st.markdown("### 📊 Global Visual Analytics")

    if total_alerts > 0:
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.markdown("#### Stock Status Distribution")
            status_counts = wh_df["Stock Status"].value_counts()
            st.bar_chart(status_counts)

        with col_g2:
            st.markdown("#### Transport Status Overview")
            if not trans_df.empty and "Transport Status" in trans_df.columns:
                trans_counts = trans_df["Transport Status"].value_counts()
                st.bar_chart(trans_counts)
            else:
                st.info("No active transport tracking records available yet.")
    else:
        st.info("ℹ️ The system is currently empty. Start by submitting alerts from the **Production** department.")

# ==========================================
# 2. PRODUCTION DEPARTMENT
# ==========================================
elif menu == "1. Production":
    st.title("🏭 Production Department")
    st.markdown("Create new stock alerts by submitting required materials and quantities for production.")
    st.markdown("---")

    with st.form(key="production_form"):
        part_material = st.text_input("Part / Material Name or Code")
        required_qty = st.number_input("Required Quantity", min_value=0.0, value=10.0, step=1.0)
        comment = st.text_area("Comment / Notes")
        
        submit_button = st.form_submit_button(label="Submit Alert to Warehouse")

        if submit_button:
            if part_material.strip() == "":
                st.error("Please enter a valid Part / Material name.")
            else:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                # Add to Production session state
                new_prod = pd.DataFrame([{
                    "Part / Material": part_material,
                    "Required Quantity": required_qty,
                    "Comment": comment,
                    "Timestamp": timestamp
                }])
                st.session_state.production_df = pd.concat([st.session_state.production_df, new_prod], ignore_index=True)

                # Automatically synchronize / push to Warehouse data if part doesn't exist or update required qty
                wh_existing = st.session_state.warehouse_df
                if part_material in wh_existing["Part / Material"].values:
                    # Update required quantity in warehouse
                    wh_existing.loc[wh_existing["Part / Material"] == part_material, "Required Quantity"] = required_qty
                else:
                    # Create new entry in warehouse with default available quantity set to 0 initially
                    new_wh = pd.DataFrame([{
                        "Part / Material": part_material,
                        "Required Quantity": required_qty,
                        "Available Quantity": 0.0,
                        "Shortage Quantity": required_qty,
                        "Stock Status": "Out of Stock",
                        "Warehouse Location": "Unassigned",
                        "Notification": "🚨 Alert: New requirement registered, currently Out of Stock.",
                        "Comments": comment
                    }])
                    st.session_state.warehouse_df = pd.concat([st.session_state.warehouse_df, new_wh], ignore_index=True)

                st.success(f"✅ Alert for '{part_material}' successfully submitted and routed to Warehouse!")
                st.rerun()

    st.markdown("### 📋 Production Requests History")
    if not st.session_state.production_df.empty:
        st.dataframe(st.session_state.production_df, width="stretch")
    else:
        st.info("No production alerts submitted yet.")

# ==========================================
# 3. WAREHOUSE OPERATIONS
# ==========================================
elif menu == "2. Warehouse":
    st.title("📦 Warehouse Operations")
    st.markdown("Manage stock availability, view automated calculations, and monitor automatic inter-departmental triggers.")
    st.markdown("---")

    if st.session_state.warehouse_df.empty:
        st.info("No stock items registered. Please create alerts in the Production department first.")
    else:
        wh_df = st.session_state.warehouse_df

        st.markdown("### ✏️ Update Stock Availability & Locations")
        edited_wh = st.data_editor(
            wh_df,
            num_rows="dynamic",
            key="warehouse_editor",
            column_config={
                "Stock Status": st.column_config.TextColumn("Stock Status (Auto)"),
                "Shortage Quantity": st.column_config.NumberColumn("Shortage (Auto)", format="%.1f"),
                "Notification": st.column_config.TextColumn("Automated Notifications")
            },
            width="stretch"
        )

        if st.button("💾 Save Stock Updates & Run Automatic Calculations"):
            # Recalculate metrics automatically based on user inputs
            updated_rows = []
            for _, row in edited_wh.iterrows():
                req = float(row.get("Required Quantity", 0))
                avail = float(row.get("Available Quantity", 0))
                
                # Automatic Shortage calculation
                shortage = req - avail
                if shortage < 0:
                    shortage = 0.0

                # Automatic Stock Status determination
                if avail == 0:
                    status = "Out of Stock"
                    notif = "🚨 OUT OF STOCK: Immediate alert sent to Procurement."
                elif avail == 1:
                    status = "Critical Stock"
                    notif = "🚨 CRITICAL STOCK (1 Unit): Automated urgent alert sent to Procurement & Production."
                elif avail < req:
                    status = "Shortage"
                    notif = f"⚠️ SHORTAGE: Missing {int(shortage)} units. Alert sent to Procurement."
                else:
                    status = "Stock Available"
                    notif = "✅ Stock Available: Requested quantity is fully covered. Notification sent to Production."

                row_dict = row.to_dict()
                row_dict["Shortage Quantity"] = shortage
                row_dict["Stock Status"] = status
                row_dict["Notification"] = notif
                updated_rows.append(row_dict)

            st.session_state.warehouse_df = pd.DataFrame(updated_rows)

            # Automatically propagate shortages to Procurement if not already present
            for _, r in st.session_state.warehouse_df.iterrows():
                if r["Stock Status"] in ["Shortage", "Critical Stock", "Out of Stock"]:
                    part = r["Part / Material"]
                    short_qty = r["Shortage Quantity"]
                    
                    proc_df = st.session_state.procurement_df
                    if part not in proc_df["Part / Material"].values:
                        new_proc = pd.DataFrame([{
                            "Part / Material": part,
                            "Shortage Quantity": short_qty,
                            "Supplier": "Pending Supplier",
                            "Purchase Order": f"PO-{datetime.now().strftime('%d%H%M%S')}-{part[:3].upper()}",
                            "Order Date": datetime.now().strftime("%Y-%m-%d"),
                            "Expected Delivery Date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                            "Procurement Status": "Pending",
                            "Comments": "Automatically generated from Warehouse shortage."
                        }])
                        st.session_state.procurement_df = pd.concat([st.session_state.procurement_df, new_proc], ignore_index=True)
                    else:
                        # Update shortage quantity if already exists
                        proc_df.loc[proc_df["Part / Material"] == part, "Shortage Quantity"] = short_qty

            st.success("✅ Warehouse data saved, calculations updated, and procurement alerts synchronized automatically!")
            st.rerun()

        st.markdown("---")
        st.download_button(
            label="📥 Download Warehouse Report",
            data=convert_df_to_excel(st.session_state.warehouse_df),
            file_name="Warehouse_Stock_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ==========================================
# 4. PROCUREMENT DEPARTMENT
# ==========================================
elif menu == "3. Procurement":
    st.title("🛒 Procurement & Supply")
    st.markdown("Review automated shortage triggers received from the Warehouse, manage suppliers, purchase orders, and delivery schedules.")
    st.markdown("---")

    proc_df = st.session_state.procurement_df

    if proc_df.empty:
        st.info("No active procurement orders or shortage alerts received from Warehouse yet.")
    else:
        st.markdown("### ✏️ Manage Procurement Orders & Suppliers")
        edited_proc = st.data_editor(
            proc_df,
            num_rows="dynamic",
            key="procurement_editor",
            width="stretch"
        )

        if st.button("💾 Save Procurement Changes & Push to Transport"):
            st.session_state.procurement_df = edited_proc

            # Automatically create or update transport tracking entries for approved orders
            for _, row in edited_proc.iterrows():
                po = row.get("Purchase Order")
                supplier = row.get("Supplier")
                qty = row.get("Shortage Quantity")
                status = row.get("Procurement Status")
                
                trans_df = st.session_state.transport_df
                
                # If order is being processed or ordered, sync to transport
                if po and po.strip() != "":
                    if po not in trans_df["Purchase Order"].values:
                        new_trans = pd.DataFrame([{
                            "Purchase Order": po,
                            "Supplier": supplier,
                            "Quantity": qty,
                            "Tracking Number": f"TRK-{datetime.now().strftime('%d%H%M')}",
                            "Shipment Date": datetime.now().strftime("%Y-%m-%d"),
                            "ETA": row.get("Expected Delivery Date", datetime.now().strftime("%Y-%m-%d")),
                            "Actual Delivery Date": "",
                            "Transport Status": "Ordered",
                            "Comments": "Synced automatically from Procurement."
                        }])
                        st.session_state.transport_df = pd.concat([st.session_state.transport_df, new_trans], ignore_index=True)
                    else:
                        # Update fields
                        trans_df.loc[trans_df["Purchase Order"] == po, "Supplier"] = supplier
                        trans_df.loc[trans_df["Purchase Order"] == po, "Quantity"] = qty

            st.success("✅ Procurement details saved and synchronized with Transport tracking successfully!")
            st.rerun()

        st.markdown("---")
        st.download_button(
            label="📥 Download Procurement Report",
            data=convert_df_to_excel(st.session_state.procurement_df),
            file_name="Procurement_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ==========================================
# 5. TRANSPORT TRACKING
# ==========================================
elif menu == "4. Transport":
    st.title("🚚 Transport Tracking")
    st.markdown("Monitor delivery routes, shipment dates, ETAs, and operational statuses (Ordered → In Transit → Delivered → Closed).")
    st.markdown("---")

    trans_df = st.session_state.transport_df

    if trans_df.empty:
        st.info("No active transport shipments available. Orders created in Procurement will appear here automatically.")
    else:
        st.markdown("### ✏️ Track Shipments & Logistics Workflow")
        edited_trans = st.data_editor(
            trans_df,
            num_rows="dynamic",
            key="transport_editor",
            column_config={
                "Transport Status": st.column_config.SelectboxColumn(
                    "Transport Status",
                    options=["Ordered", "In Transit", "Delivered", "Closed"],
                    required=True
                )
            },
            width="stretch"
        )

        if st.button("💾 Save Transport Tracking Updates"):
            st.session_state.transport_df = edited_trans
            st.success("✅ Transport tracking updates saved successfully!")
            st.rerun()

        st.markdown("---")
        st.download_button(
            label="📥 Download Transport Report",
            data=convert_df_to_excel(st.session_state.transport_df),
            file_name="Transport_Tracking_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
