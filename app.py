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

    wh_df = st.session_state.warehouse_df
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

    with st.expander("➕ Add New Production Alert", expanded=True):
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

                    # Automatically synchronize / push to Warehouse data
                    wh_existing = st.session_state.warehouse_df
                    if not wh_existing.empty and part_material in wh_existing["Part / Material"].values:
                        wh_existing.loc[wh_existing["Part / Material"] == part_material, "Required Quantity"] = required_qty
                    else:
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
    st.markdown("Manage stock availability, view automated calculations, and add warehouse items directly.")
    st.markdown("---")

    with st.expander("➕ Add New Warehouse Item"):
        with st.form(key="warehouse_add_form"):
            wh_part = st.text_input("Part / Material Name")
            wh_req = st.number_input("Required Quantity", min_value=0.0, value=10.0, step=1.0)
            wh_avail = st.number_input("Available Quantity", min_value=0.0, value=0.0, step=1.0)
            wh_loc = st.text_input("Warehouse Location (e.g., Zone A-12)")
            wh_comment = st.text_area("Comments")
            
            add_wh_btn = st.form_submit_button(label="Add Item to Warehouse")
            if add_wh_btn:
                if wh_part.strip() == "":
                    st.error("Please enter a part name.")
                else:
                    shortage = max(0.0, wh_req - wh_avail)
                    if wh_avail == 0:
                        status = "Out of Stock"
                        notif = "🚨 OUT OF STOCK: Immediate alert sent to Procurement."
                    elif wh_avail == 1:
                        status = "Critical Stock"
                        notif = "🚨 CRITICAL STOCK (1 Unit): Automated urgent alert sent."
                    elif wh_avail < wh_req:
                        status = "Shortage"
                        notif = f"⚠️ SHORTAGE: Missing {int(shortage)} units."
                    else:
                        status = "Stock Available"
                        notif = "✅ Stock Available: Fully covered."

                    new_row = pd.DataFrame([{
                        "Part / Material": wh_part,
                        "Required Quantity": wh_req,
                        "Available Quantity": wh_avail,
                        "Shortage Quantity": shortage,
                        "Stock Status": status,
                        "Warehouse Location": wh_loc,
                        "Notification": notif,
                        "Comments": wh_comment
                    }])
                    st.session_state.warehouse_df = pd.concat([st.session_state.warehouse_df, new_row], ignore_index=True)
                    st.success("Item added successfully!")
                    st.rerun()

    if st.session_state.warehouse_df.empty:
        st.info("No stock items registered. Please create alerts in the Production department or use the Add button above.")
    else:
        wh_df = st.session_state.warehouse_df

        st.markdown("### 📋 Stock Table & Availability Management")
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
            updated_rows = []
            for _, row in edited_wh.iterrows():
                req = float(row.get("Required Quantity", 0))
                avail = float(row.get("Available Quantity", 0))
                
                shortage = req - avail
                if shortage < 0:
                    shortage = 0.0

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
                    notif = "✅ Stock Available: Requested quantity is fully covered."

                row_dict = row.to_dict()
                row_dict["Shortage Quantity"] = shortage
                row_dict["Stock Status"] = status
                row_dict["Notification"] = notif
                updated_rows.append(row_dict)

            st.session_state.warehouse_df = pd.DataFrame(updated_rows)

            # Automatically propagate shortages to Procurement
            for _, r in st.session_state.warehouse_df.iterrows():
                if r["Stock Status"] in ["Shortage", "Critical Stock", "Out of Stock"]:
                    part = r["Part / Material"]
                    short_qty = r["Shortage Quantity"]
                    
                    proc_df = st.session_state.procurement_df
                    if proc_df.empty or part not in proc_df["Part / Material"].values:
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
    st.markdown("Review automated shortage triggers received from the Warehouse, manage suppliers, and add purchase orders.")
    st.markdown("---")

    with st.expander("➕ Add New Purchase Order"):
        with st.form(key="proc_add_form"):
            p_part = st.text_input("Part / Material")
            p_qty = st.number_input("Shortage / Order Quantity", min_value=0.0, value=10.0, step=1.0)
            p_supp = st.text_input("Supplier Name")
            p_po = st.text_input("Purchase Order Number (e.g., PO-1001)")
            p_ord_date = st.date_input("Order Date", value=datetime.now())
            p_exp_date = st.date_input("Expected Delivery Date", value=datetime.now() + timedelta(days=7))
            p_status = st.selectbox("Procurement Status", ["Pending", "Approved", "Ordered", "Completed"])
            p_comm = st.text_area("Comments")
            
            add_proc_btn = st.form_submit_button(label="Create Purchase Order")
            if add_proc_btn:
                if p_po.strip() == "":
                    st.error("Please provide a Purchase Order number.")
                else:
                    new_p_row = pd.DataFrame([{
                        "Part / Material": p_part,
                        "Shortage Quantity": p_qty,
                        "Supplier": p_supp,
                        "Purchase Order": p_po,
                        "Order Date": p_ord_date.strftime("%Y-%m-%d"),
                        "Expected Delivery Date": p_exp_date.strftime("%Y-%m-%d"),
                        "Procurement Status": p_status,
                        "Comments": p_comm
                    }])
                    st.session_state.procurement_df = pd.concat([st.session_state.procurement_df, new_p_row], ignore_index=True)
                    st.success("Purchase order added successfully!")
                    st.rerun()

    proc_df = st.session_state.procurement_df

    if proc_df.empty:
        st.info("No active procurement orders or shortage alerts received from Warehouse yet.")
    else:
        st.markdown("### 📋 Procurement Orders Management")
        edited_proc = st.data_editor(
            proc_df,
            num_rows="dynamic",
            key="procurement_editor",
            width="stretch"
        )

        if st.button("💾 Save Procurement Changes & Push to Transport"):
            st.session_state.procurement_df = edited_proc

            for _, row in edited_proc.iterrows():
                po = row.get("Purchase Order")
                supplier = row.get("Supplier")
                qty = row.get("Shortage Quantity")
                
                trans_df = st.session_state.transport_df
                if po and po.strip() != "":
                    if trans_df.empty or po not in trans_df["Purchase Order"].values:
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
    st.markdown("Monitor delivery routes, shipment statuses, and add direct transport tracking entries.")
    st.markdown("---")

    with st.expander("➕ Add New Shipment Tracking"):
        with st.form(key="trans_add_form"):
            t_po = st.text_input("Purchase Order Number")
            t_supp = st.text_input("Supplier Name")
            t_qty = st.number_input("Quantity", min_value=0.0, value=10.0, step=1.0)
            t_trk = st.text_input("Tracking Number (e.g., TRK-9842)")
            t_ship_date = st.date_input("Shipment Date", value=datetime.now())
            t_eta = st.date_input("Estimated Time of Arrival (ETA)", value=datetime.now() + timedelta(days=5))
            t_status = st.selectbox("Transport Status", ["Ordered", "In Transit", "Delivered", "Closed"])
            t_comm = st.text_area("Comments")
            
            add_trans_btn = st.form_submit_button(label="Add Shipment")
            if add_trans_btn:
                if t_po.strip() == "":
                    st.error("Please provide a Purchase Order reference.")
                else:
                    new_t_row = pd.DataFrame([{
                        "Purchase Order": t_po,
                        "Supplier": t_supp,
                        "Quantity": t_qty,
                        "Tracking Number": t_trk,
                        "Shipment Date": t_ship_date.strftime("%Y-%m-%d"),
                        "ETA": t_eta.strftime("%Y-%m-%d"),
                        "Actual Delivery Date": "",
                        "Transport Status": t_status,
                        "Comments": t_comm
                    }])
                    st.session_state.transport_df = pd.concat([st.session_state.transport_df, new_t_row], ignore_index=True)
                    st.success("Shipment added successfully!")
                    st.rerun()

    trans_df = st.session_state.transport_df

    if trans_df.empty:
        st.info("No active transport shipments available. Orders created in Procurement will appear here automatically.")
    else:
        st.markdown("### 📋 Active Shipments & Logistics Workflow")
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
