import streamlit as st
import pandas as pd

# Load Data
@st.cache_data
def load_data():
    df_contracts = pd.read_csv("Matched_Contracts.csv", dtype=str)  # Contracts data
    df_registry = pd.read_csv("cleaned_contractors.csv", dtype=str)  # Contractor registry data
    return df_contracts, df_registry

df_contracts, df_registry = load_data()

# Initialize session state for selected business
if "selected_business" not in st.session_state:
    st.session_state.selected_business = None

# Title of the App
st.title("🏗️ Contractor Profile Lookup")

# Search bar (Name or Address)
search_term = st.text_input("🔍 Enter Contractor Name or Address:", "").upper().strip()

# Automatically search if a name or address is entered
if search_term:
    registry_results = df_registry[
        df_registry["Business Name"].str.contains(search_term, na=False, case=False) |
        df_registry["Address"].str.contains(search_term, na=False, case=False)
    ]

    if not registry_results.empty:
        # Store available businesses in session state
        st.session_state.business_list = registry_results["Business Name"].unique()

        # If multiple businesses match, show dropdown
        if len(st.session_state.business_list) > 1:
            st.session_state.selected_business = st.selectbox(
                "Multiple businesses found. Please select one before continuing:", 
                st.session_state.business_list,
                index=0  # Default to first business in list
            )
        else:
            # If only one business matches, select it automatically
            st.session_state.selected_business = st.session_state.business_list[0]

# Keep the dropdown visible and display details if a selection exists
if st.session_state.selected_business:
    business_data = df_registry[df_registry["Business Name"] == st.session_state.selected_business]

    # Display Business Profile
    if not business_data.empty:
        st.subheader(f"📌 Business Profile for {st.session_state.selected_business}")
        first_result = business_data.iloc[0]

        st.write(f"🏢 **Business Name:** {first_result['Business Name']}")
        st.write(f"📍 **Address:** {first_result.get('Address', 'N/A')}")
        st.write(f"📍 **City, State, ZIP:** {first_result.get('City', 'N/A')}, {first_result.get('State', 'N/A')} {first_result.get('Zip Code', 'N/A')}")
        st.write(f"📞 **Phone:** {first_result.get('Phone', 'N/A')}")
        st.write(f"🏢 **MBE Status:** {first_result.get('Business is MWBE Owned', 'N/A')}")
        st.write(f"🚫 **Debarment:** {first_result.get('Business has been debarred', 'N/A')}")
        st.write(f"🏗️ **Apprenticeship Program:** {first_result.get('Business is associated with an apprenticeship program', 'N/A')}")

        # Check Violations
        labor_violation = first_result.get("Business has final determination for violation of Labor or Tax Law", "No")
        safety_violation = first_result.get("Business has final determination safety standard violations", "No")
        wage_violation = first_result.get("Business has outstanding wage assessments", "No")

        violations_list = []
        if labor_violation == "Yes":
            violations_list.append("⚠️ Labor/Tax Law Violation")
        if safety_violation == "Yes":
            violations_list.append("⚠️ Safety Standard Violation")
        if wage_violation == "Yes":
            violations_list.append("⚠️ Outstanding Wage Assessments")

        violations_text = " | ".join(violations_list) if violations_list else "✅ No known violations"

        st.write(f"⚠️ **Violations:** {violations_text}")

        # Search for contracts related to the selected business
        contract_results = df_contracts[
            (df_contracts["Prime Vendor Match"].str.contains(st.session_state.selected_business, na=False, case=False)) |
            (df_contracts["Sub Vendor Match"].str.contains(st.session_state.selected_business, na=False, case=False))
        ]

        # Convert contract amount to float and calculate the total sum
        contract_results["Prime Contract Current Amount"] = (
            contract_results["Prime Contract Current Amount"]
            .str.replace(",", "", regex=True)  # Remove commas
            .astype(float)  # Convert to float
        )

        total_contract_amount = contract_results["Prime Contract Current Amount"].sum()

        # Display contracts if found
        if not contract_results.empty:
            st.subheader(f"📑 Associated Contracts")
            st.write(f"💰 **Total Contract Amount:** ${total_contract_amount:,.2f}")  # Display total amount formatted

            st.dataframe(contract_results[[
                "Prime Contract ID", "Prime Contract Current Amount",
                "Prime Contract Start Date", "Prime Contract End Date",
                "Prime Contracting Agency"
            ]])
        else:
            st.warning("❌ No contracts found for this contractor.")

else:
    st.warning("⚠️ Please enter a business name or address.")
