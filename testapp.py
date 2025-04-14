import streamlit as st
import pandas as pd
from datetime import datetime

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
    "Wage Theft": "company_name",
    "Construction Apprentice": "sponsor"
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
st.title("\U0001F3D7\uFE0F Contractor Profile Lookup")

# === USER SEARCH INPUT ===
search_option = st.radio("Search by:", ["Business Name", "Address"], horizontal=True)
search_term = st.text_input(f"\U0001F50D Enter {search_option}").strip().upper()

if "selected_business" not in st.session_state:
    st.session_state.selected_business = None

# === SEARCH LOGIC ===
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
    st.subheader(f"\U0001F4CC Profile for: {selected_name}")

    row = data["registry"][data["registry"]["Business Name"] == selected_name].iloc[0]

    # === VIOLATION FLAGS AT TOP ===
    flags = []
    if row.get("Business has final determination for violation of Labor or Tax Law", "No").strip().lower() == "yes":
        flags.append("⚠️ Labor or Tax Law Violation")
    if row.get("Business has final determination safety standard violations", "No").strip().lower() == "yes":
        flags.append("⚠️ Safety Standard Violation")
    if row.get("Business has outstanding wage assessments", "No").strip().lower() == "yes":
        flags.append("⚠️ Outstanding Wage Assessments")
    if row.get("Business has been debarred", "No").strip().lower() == "yes":
        flags.append("🚫 Debarment Record")

    if flags:
        for flag in flags:
            st.markdown(flag)

    # === 1. Contractor Registry ===
    with st.expander("\U0001F3E2 Business Registration Details"):
        sheet = data["metadata"]["NYS Contractor Registry"]
        fields = sheet[sheet["Display?"].astype(str).str.lower().str.contains("x|yes|if data", na=False)]

        not_applicable_skip_fields = [
            "Reason business does not have a NYS DOL Employer Registration Number",
            "Debarment State or Federal Law",
            "Debarment State",
            "Debarment Start Date",
            "Debarment End Date",
            "Business has outstanding wage assessments",
            "Business has been debarred",
            "Business has final determination for violation of Labor or Tax Law",
            "Business has final determination safety standard violations"
        ]

        for _, r in fields.iterrows():
            label = r["Data Label"]
            rule = str(r["Display?"]).strip().lower()
            value = str(row.get(label, "")).strip()

            if label in not_applicable_skip_fields:
                continue

            if label == "Business is exempt from Workers Compensation Insurance" and value.lower() != "yes":
                continue

            if rule == "x":
                st.write(f"**{label}:** {value if value else 'N/A'}")
            elif rule == "if yes" and value.lower() == "yes":
                st.write(f"**{label}:** Yes")
            elif rule == "if data" and value:
                st.write(f"**{label}:** {value}")

    # === 2. NYC Contracts ===
    with st.expander("\U0001F4BC NYC Prime & Subcontract Awards"):
        contracts = data["contracts"]
        contract_rows = contracts[
            (contracts["Prime Vendor"].str.contains(selected_name, na=False)) |
            (contracts["Sub Vendor"].str.contains(selected_name, na=False))
        ]
        if not contract_rows.empty:
            sheet = data["metadata"]["NYC Awarded Contracts"]
            fields = sheet[sheet["Display?"].astype(str).str.lower().str.strip() == "x"]["Field"].tolist()
            for _, row in contract_rows.iterrows():
                st.markdown("---")
                for field in fields:
                    value = row.get(field, "")
                    if pd.notna(value) and value.strip() != "":
                        st.write(f"**{field}:** {value}")
        else:
            st.write("✅ No awarded contracts found for this business.")

    # === 3. Violation and Wage Theft Records ===
    with st.expander("⚖️ Violation and Wage Theft Records"):
        show_no_violation = True
        registry_row = row
        violations = []

        for label in [
            "Debarment State or Federal Law",
            "Debarment State",
            "Debarment Start Date",
            "Debarment End Date",
            "Business has outstanding wage assessments",
            "Business has been debarred",
            "Business has final determination for violation of Labor or Tax Law",
            "Business has final determination safety standard violations"
        ]:
            val = registry_row.get(label, "").strip()
            if val and val.lower() != "not applicable" and val.lower() != "no":
                st.write(f"**{label}:** {val}")
                show_no_violation = False

        theft_df = data["wagetheft"]
        wage_violation_found = False
        if "company_name" in theft_df.columns:
            theft_df["company_name_cleaned"] = theft_df["company_name"].str.upper().str.strip()
            theft_matches = theft_df[theft_df["company_name_cleaned"] == selected_name.upper().strip()]
            if not theft_matches.empty:
                wage_violation_found = True
                for _, row in theft_matches.iterrows():
                    st.markdown("---")
                    for col in ["industry", "date", "claimants", "wages_stolen"]:
                        value = row.get(col, "")
                        if col == "date":
                            try:
                                value = datetime.fromtimestamp(float(value)/1000).strftime("%B %d, %Y")
                            except:
                                pass
                        if pd.notna(value) and value.strip() != "":
                            st.write(f"**{col.replace('_', ' ').title()}:** {value}")

        if show_no_violation and not wage_violation_found:
            st.success("✅ No known violations on file.")

    # === 4. Apprenticeship ===
    with st.expander("\U0001F477 Apprenticeship Program Participation Details"):
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
