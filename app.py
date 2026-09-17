import streamlit as st
import pandas as pd
import datetime

# Configuration de la page
st.set_page_config(
    page_title="Gestion des Alertes de Stock & Supply Chain",
    page_icon="🚨",
    layout="wide"
)

# --- CHARGEMENT / SAUVEGARDE DES DONNÉES ---
EXCEL_FILE = 'Production1_Alerts_Dashboard.xlsx'

@st.cache_data(ttl=1)
def load_data():
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name='Alerts Data')
    except Exception:
        df = pd.DataFrame([{
            'Alert No.': 'ALT-001',
            'Part Number': 'GR129862',
            'Alert Date': datetime.date.today(),
            'Description': 'GROMMET 78828914',
            'Required Quantity': 9,
            'Production Line': 'Line 1',
            'Status': 'Nouvelle',
            'Priorité': 'Haute',
            'Available Stock': 0,
            'Root cause': 'Missing Part',
            'Action Required By': 'Logistique',
            'Logistics Feedback': '',
            'Procurement Feedback': '',
            'Transport Feedback': '',
            'Close Date': None,
            'Production Comments': 'Besoin urgent pour arrêt de ligne.'
        }])
    return df

if 'data' not in st.session_state:
    st.session_state.data = load_data()

def save_data():
    with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
        st.session_state.data.to_excel(writer, sheet_name='Alerts Data', index=False)

# --- BARRE LATÉRALE / FILTRES ---
st.sidebar.title("Supply Chain Control")

menu = st.sidebar.radio(
    "Navigation", 
    ["📊 Tableau de Bord", "🚨 Nouvelle Alerte (Production)", "⚙️ Traitement Multi-Services", "📜 Historique & Export"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Filtres")
status_filter = st.sidebar.multiselect("Statut", options=st.session_state.data['Status'].unique(), default=st.session_state.data['Status'].unique())
line_filter = st.sidebar.multiselect("Ligne de Production", options=st.session_state.data['Production Line'].dropna().unique())

filtered_df = st.session_state.data.copy()
if status_filter:
    filtered_df = filtered_df[filtered_df['Status'].isin(status_filter)]
if line_filter:
    filtered_df = filtered_df[filtered_df['Production Line'].isin(line_filter)]

# --- PAGE 1 : TABLEAU DE BORD ---
if menu == "📊 Tableau de Bord":
    st.title("📊 Tableau de Bord des Alertes & Stocks")
    
    col1, col2, col3, col4 = st.columns(4)
    total_alerts = len(st.session_state.data)
    new_alerts = len(st.session_state.data[st.session_state.data['Status'] == 'Nouvelle'])
    in_progress = len(st.session_state.data[st.session_state.data['Status'].str.startswith('En cours', na=False)])
    resolved = len(st.session_state.data[st.session_state.data['Status'] == 'Résolue'])

    col1.metric("Total Alertes", total_alerts)
    col2.metric("Nouvelles Alertes", new_alerts)
    col3.metric("En Cours de Traitement", in_progress)
    col4.metric("Alertes Résolues", resolved)

    st.markdown("---")
    
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Alertes par Statut")
        st.bar_chart(st.session_state.data['Status'].value_counts())

    with col_right:
        st.subheader("Alertes par Ligne de Production")
        st.bar_chart(st.session_state.data['Production Line'].value_counts())

    st.subheader("📋 Liste des Alertes Actives")
    st.dataframe(filtered_df[['Alert No.', 'Part Number', 'Description', 'Required Quantity', 'Production Line', 'Status', 'Action Required By']], use_container_width=True)

# --- PAGE 2 : CRÉATION D'ALERTE (PRODUCTION) ---
elif menu == "🚨 Nouvelle Alerte (Production)":
    st.title("🚨 Signaler une Alerte de Stock / Composant")
    
    with st.form("new_alert_form"):
        col1, col2 = st.columns(2)
        with col1:
            part_num = st.text_input("Référence Pièce (Part Number)*")
            desc = st.text_input("Description / Désignation*")
            qty = st.number_input("Quantité Requise*", min_value=1, value=1)
            p_line = st.selectbox("Ligne de Production*", ["Line 1", "Line 2", "Line 3", "Line 4"])
        
        with col2:
            priority = st.selectbox("Priorité", ["Basse", "Moyenne", "Haute", "Critique (Arrêt Ligne)"])
            root_cause = st.selectbox("Cause Racine Suspectée", ["Missing Part", "Late Delivery", "Quality Issue", "Inventory Discrepancy", "Other"])
            comments = st.text_area("Commentaires Production")

        submitted = st.form_submit_button("Lancer l'Alerte")
        
        if submitted:
            if not part_num or not desc:
                st.error("Veuillez remplir les champs obligatoires (*)")
            else:
                alert_id = f"ALT-{len(st.session_state.data) + 1:03d}"
                new_row = {
                    'Alert No.': alert_id,
                    'Part Number': part_num,
                    'Alert Date': datetime.date.today().strftime('%Y-%m-%d'),
                    'Description': desc,
                    'Required Quantity': qty,
                    'Production Line': p_line,
                    'Status': 'Nouvelle',
                    'Priorité': priority,
                    'Available Stock': 0,
                    'Root cause': root_cause,
                    'Action Required By': 'Logistique',
                    'Logistics Feedback': '',
                    'Procurement Feedback': '',
                    'Transport Feedback': '',
                    'Close Date': None,
                    'Production Comments': comments
                }
                st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=False)
                save_data()
                st.success(f"Alerte {alert_id} créée avec succès !")

# --- PAGE 3 : TRAITEMENT MULTI-SERVICES ---
elif menu == "⚙️ Traitement Multi-Services":
    st.title("⚙️ Suivi & Traitement Inter-Services")
    
    alert_list = st.session_state.data['Alert No.'].tolist()
    selected_alert_id = st.selectbox("Sélectionner une Alerte à traiter :", alert_list)
    
    alert_idx = st.session_state.data[st.session_state.data['Alert No.'] == selected_alert_id].index[0]
    row = st.session_state.data.loc[alert_idx]

    st.info(f"**Alerte:** {row['Alert No.']} | **Article:** {row['Part Number']} ({row['Description']}) | **Besoin:** {row['Required Quantity']} pcs sur {row['Production Line']}")

    tab_log, tab_proc, tab_trans, tab_close = st.tabs(["📦 Logistique", "🛒 Approvisionnement", "🚚 Transport", "✅ Clôture"])

    with tab_log:
        st.subheader("Module Logistique")
        avail_stock = st.number_input("Stock Disponible Reel", value=int(row['Available Stock'] or 0))
        log_fb = st.text_area("Feedback Logistique", value=str(row['Logistics Feedback'] or ''))
        if st.button("Mettre à jour Logistique"):
            st.session_state.data.loc[alert_idx, 'Available Stock'] = avail_stock
            st.session_state.data.loc[alert_idx, 'Logistics Feedback'] = log_fb
            st.session_state.data.loc[alert_idx, 'Status'] = 'En cours (Logistique)'
            st.session_state.data.loc[alert_idx, 'Action Required By'] = 'Approvisionnement' if avail_stock < row['Required Quantity'] else 'Production'
            save_data()
            st.success("Mise à jour Logistique enregistrée !")

    with tab_proc:
        st.subheader("Module Approvisionnement")
        proc_fb = st.text_area("Feedback Approvisionnement (Commande / Delais)", value=str(row['Procurement Feedback'] or ''))
        if st.button("Mettre à jour Approvisionnement"):
            st.session_state.data.loc[alert_idx, 'Procurement Feedback'] = proc_fb
            st.session_state.data.loc[alert_idx, 'Status'] = 'En cours (Appro)'
            st.session_state.data.loc[alert_idx, 'Action Required By'] = 'Transport'
            save_data()
            st.success("Mise à jour Approvisionnement enregistrée !")

    with tab_trans:
        st.subheader("Module Transport & Expeditions")
        trans_fb = st.text_area("Feedback Transport (Tracking / Date livraison)", value=str(row['Transport Feedback'] or ''))
        if st.button("Mettre à jour Transport"):
            st.session_state.data.loc[alert_idx, 'Transport Feedback'] = trans_fb
            st.session_state.data.loc[alert_idx, 'Status'] = 'En cours (Transport)'
            save_data()
            st.success("Mise à jour Transport enregistrée !")

    with tab_close:
        st.subheader("Clôture de l'Alerte")
        if st.button("🔒 Marquer l'Alerte comme Résolue"):
            st.session_state.data.loc[alert_idx, 'Status'] = 'Résolue'
            st.session_state.data.loc[alert_idx, 'Close Date'] = datetime.date.today().strftime('%Y-%m-%d')
            st.session_state.data.loc[alert_idx, 'Action Required By'] = 'Terminé'
            save_data()
            st.success("Alerte clôturée avec succès !")

# --- PAGE 4 : HISTORIQUE ET EXPORT ---
elif menu == "📜 Historique & Export":
    st.title("📜 Historique Complet des Alertes")
    st.dataframe(st.session_state.data, use_container_width=True)
    
    csv = st.session_state.data.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Télécharger l'historique (CSV/Excel)", csv, "Alerts_History.csv", "text/csv")