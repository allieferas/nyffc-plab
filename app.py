import streamlit as st
import pandas as pd
from pathlib import Path
import sqlite3 as sql

# MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(page_title="Contractor Profile Lookup", layout="wide")

# === FILE LOCATIONS ===
project_dir = Path(__file__).parent.parent
db_path = project_dir.joinpath("data","out", "nyffc.db")
conn = sql.connect(db_path)
cur = conn.cursor()

# === DISPLAY COLUMN MAP (per sheet) ===
display_column_map = {
    "NYC Awarded Contracts": "Field",
    "NYS Contractor Registry": "Data Label",
    "Wage Theft": "company_name",  # updated from "Name"
    "Construction Apprentice": "sponsor"  # updated from "Name"
}

# === LOAD DATA ===
@st.cache_data # TODO: is this needed with db vs csvs?
def load_contractors(_connection):
    df = pd.read_sql_query("SELECT * FROM name", _connection)
    df['NAME'] = df['NAME1'] + (" (" + df['NAME2'] + ")").replace(" ()", "")
    df['DISPLAY'] = df['NAME'] + (", " + df['ADDRESS']).replace(r", $","",regex=True)
    return df

contractors = load_contractors(conn)

def get_details(company_id,fact_table, _connection):
    df = pd.read_sql_query(
        f"""SELECT n2.NAME1, n2.NAME2, n2.ADDRESS, f.*
        FROM NAME n1
        JOIN MATCH m on m.company_id = n1.company_id
        join NAME n2 on n2.company_id = m.company_match
        join {fact_table} f on f.company_id = n2.company_id
        where n1.company_id = {company_id}""",
        _connection)
    df['DISPLAY'] = df['NAME1'] + (" (" + df['NAME2'] + ")").replace(" ()", "") + (", " + df['ADDRESS']).replace(r", $","",regex=True)
    return df

# === TITLE ===
st.title("🏗️ Contractor Profile Lookup")

# === USER SEARCH INPUT ===
search_option = st.radio("Search by:", ["Contractor Name", "Address"], horizontal=True)
search_term = st.text_input(f"🔍 Enter {search_option}").strip().upper()

# Initialize session state
if "selected_business" not in st.session_state:
    st.session_state.selected_business = None
if "selected_id" not in st.session_state:
    st.session_state.selected_id = None

# === SEARCH AND SELECTION LOGIC ===
if search_term:
    if search_option == "Contractor Name":
        matches = contractors[
            contractors['NAME'].str.contains(search_term)
        ]
    else:
        matches = contractors[contractors["ADDRESS"].str.contains(search_term, na=False, case=False)]


    if not matches.empty:
        options = matches["DISPLAY"].dropna().drop_duplicates()
        st.session_state.business_list = options.values.tolist() #TODO: what to display/formatting names and addr
        if len(st.session_state.business_list) > 1:
            st.session_state.selected_business = st.selectbox("Multiple matches found. Please select one:", st.session_state.business_list)
        else:
            st.session_state.selected_business = st.session_state.business_list[0]
        st.session_state.selected_id = matches.index[st.session_state.business_list.index(st.session_state.selected_business)]
    else:
        st.warning("No matches found.")

# === PROFILE OUTPUT ===
if st.session_state.selected_business:
    st.markdown(f"##### 📌 Profile for: {st.session_state.selected_business}")

    # === 1. Contractor Registry ===
    registry_data = get_details(st.session_state.selected_id, 'REGISTRY', conn) #TODO handle if empty
    if not registry_data.empty:
        for _, r in registry_data.iterrows():
            with st.expander("🏢 Contractor Registry Details - " + r.get('DISPLAY')):
                for c in registry_data.columns:
                    value = str(r.get(c, "N/A"))
                    if pd.notna(value) and value.strip() != "":
                        st.write(f"**{c}:** {value}")

    # === 2. Debarment ===
    debar_data = get_details(st.session_state.selected_id, 'DEBARMENT', conn) #TODO handle if empty
    if not debar_data.empty:
        for _, r in debar_data.iterrows():
            with st.expander("❗Debarment Details - " + r.get('DISPLAY')):
                for c in debar_data.columns:
                    value = str(r.get(c, "N/A"))
                    if pd.notna(value) and value.strip() != "":
                        st.write(f"**{c}:** {value}")

    # === 2. NYC Contracts ===
    with st.expander("💼 NYC Prime & Subcontract Awards"):
        contracts = data["contracts"]
        contract_rows = contracts[
            (contracts["Prime Vendor"].str.contains(selected_name, na=False)) |
            (contracts["Sub Vendor"].str.contains(selected_name, na=False))
        ]
        if not contract_rows.empty:
            sheet = data["metadata"]["NYC Awarded Contracts"]
            fields = sheet[sheet["Display?"].astype(str).str.lower().str.strip() == "x"]["Field"].tolist()
            for i, row in contract_rows.iterrows():
                st.markdown("---")
                for field in fields:
                    value = row.get(field, "")
                    if pd.notna(value) and value.strip() != "":
                        st.write(f"**{field}:** {value}")
        else:
            st.write("✅ No awarded contracts found for this business.")

    # === 3. Wage Theft ===
    with st.expander("❗ Wage Investigations Linked to Business"):
        theft_df = data["wagetheft"]
        if "company_name" in theft_df.columns:
            theft_matches = theft_df[theft_df["company_name"].str.contains(selected_name, na=False)]
            if not theft_matches.empty:
                sheet = data["metadata"]["Wage Theft"]
                fields = sheet[sheet["Display?"].astype(str).str.lower().str.strip() == "x"]["Name"].tolist()
                for _, row in theft_matches.iterrows():
                    st.markdown("---")
                    for field in fields:
                        value = row.get(field, "")
                        if pd.notna(value) and value.strip() != "":
                            st.write(f"**{field}:** {value}")
            else:
                st.write("✅ No wage violation records found.")
        else:
            st.error("⚠️ Column 'company_name' not found in Wage Theft data.")

    # === 4. Apprenticeship ===
    with st.expander("👷 Apprenticeship Program Participation Details"):
        app_df = data["apprentice"]
        if "sponsor" in app_df.columns:
            app_matches = app_df[app_df["sponsor"].str.contains(selected_name, na=False)]
            if not app_matches.empty:
                sheet = data["metadata"]["Construction Apprentice"]
                fields = sheet[sheet["Display?"].astype(str).str.lower().str.strip() == "x"]["Name"].tolist()
                for _, row in app_matches.iterrows():
                    st.markdown("---")
                    for field in fields:
                        value = row.get(field, "")
                        if pd.notna(value) and value.strip() != "":
                            st.write(f"**{field}:** {value}")
            else:
                st.write("❌ This contractor is not listed in any apprenticeship program records.")
        else:
            st.error("⚠️ Column 'sponsor' not found in Apprenticeship data.")
    