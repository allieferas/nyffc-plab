import streamlit as st
import pandas as pd

# MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(page_title="Contractor Profile Lookup", layout="wide")

# === FILE LOCATIONS ===
EXCEL_METADATA = "Data Sources.xlsx"
CONTRACTOR_REGISTRY = "cleaned_contractors.csv"
AWARDED_CONTRACTS = "Matched_Contracts.csv"
NYC_AWARDS = "Cleaned_NYC_Awarded_Contracts.csv"
WAGE_THEFT = "cleaned_construction_nywagetheft.xlsx"
APPRENTICE = "cleaned_apprentice.xlsx"

# === DISPLAY COLUMN MAP (per sheet) ===
display_column_map = {
    "NYC Awarded Contracts": "Field",
    "NYS Contractor Registry": "Data Label",
    "Wage Theft": "company_name",  # updated from "Name"
    "Construction Apprentice": "sponsor"  # updated from "Name"
}

# === LOAD DATA ===
@st.cache_data
def load_all_data():
    return {
        "registry": pd.read_csv(CONTRACTOR_REGISTRY, dtype=str),
        "contracts": pd.read_csv(AWARDED_CONTRACTS, dtype=str),
        "awards": pd.read_csv(NYC_AWARDS, dtype=str),
        "wagetheft": pd.read_excel(WAGE_THEFT, dtype=str),
        "apprentice": pd.read_excel(APPRENTICE, dtype=str),
        "metadata": pd.read_excel(EXCEL_METADATA, sheet_name=None)
    }

data = load_all_data()

# === TITLE ===
st.title("🏗️ Contractor Profile Lookup")

# === USER SEARCH INPUT ===
search_option = st.radio("Search by:", ["Business Name", "Address"], horizontal=True)
search_term = st.text_input(f"🔍 Enter {search_option}").strip().upper()

# Initialize session state
if "selected_business" not in st.session_state:
    st.session_state.selected_business = None

# === SEARCH AND SELECTION LOGIC ===
if search_term:
    df_registry = data["registry"]
    if search_option == "Business Name":
        matches = df_registry[df_registry["Business Name"].str.contains(search_term, na=False, case=False)]
    else:
        matches = df_registry[df_registry["Address"].str.contains(search_term, na=False, case=False)]

    if not matches.empty:
        st.session_state.business_list = matches["Business Name"].dropna().unique()
        if len(st.session_state.business_list) > 1:
            st.session_state.selected_business = st.selectbox("Multiple matches found. Please select one:", st.session_state.business_list)
        else:
            st.session_state.selected_business = st.session_state.business_list[0]
    else:
        st.warning("No matches found.")

# === PROFILE OUTPUT ===
if st.session_state.selected_business:
    selected_name = st.session_state.selected_business
    st.subheader(f"📌 Profile for: {selected_name}")

    # === 1. Contractor Registry ===
    with st.expander("🏢 Business Registration Details"):
        business_data = data["registry"]
        match = business_data[business_data["Business Name"] == selected_name]
        if not match.empty:
            row = match.iloc[0]
            sheet = data["metadata"]["NYS Contractor Registry"]
            fields = sheet[sheet["Display?"].astype(str).str.lower().str.contains("x|yes|if data", na=False)]
            for _, r in fields.iterrows():
                label = r["Data Label"]
                value = row.get(label, "N/A")
                if pd.notna(value) and value.strip() != "":
                    st.write(f"**{label}:** {value}")
        else:
            st.info("No Contractor Registry data found.")

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
