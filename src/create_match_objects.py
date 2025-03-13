# %%
import sys
import os
from mapping import CompanyMap, OneMapToRuleThemAll
import pandas as pd
import joblib


# %% [markdown]
# ## Registry

# %%
reg = pd.read_csv("data/processed/cleaned_contractors.csv") 
reg

# %%
reg['Address 2'] = reg['Address 2'].str.replace('NOT APPLICABLE', '')
reg['DBA Name'] = reg['DBA Name'].str.replace('NO DBA', '')
reg['ADDRESS'] = reg['Address'].fillna("") + " " + reg['Address 2'].fillna("") + " " + reg['City'].fillna("") + " " + reg['State'].fillna("") + " " + reg['Zip Code'].fillna("")

reg_map = CompanyMap(
    target_data=reg,
    name_cols=['Business Name','DBA Name'],
    addr_col='ADDRESS',
    ref_name='Registry'
)

joblib.dump(reg_map, 'data/out/RegistryMap.joblib')

# %% [markdown]
# ## Debarment

# %%
debar = pd.read_csv('data/processed/NYSDOL_debarment_02_19_2025.csv')
debar

# %%
debar_map = CompanyMap(
    target_data=debar,
    name_cols=['EMPLOYER_NAME','EMPLOYER_DBA'],
    addr_col='ADDRESS',
    ref_name='Debarment'
)

joblib.dump(debar_map,"data/out/DebarmentMap.joblib")

# %% [markdown]
# ## Apprentice Signatories

# %%
sig = pd.read_csv('data/processed/cleaned_apprentice.csv')
sig

# %%
sig['ADDRESS'] = sig['signatory_address'].fillna("") + " " + sig['city'].fillna("") + " " + sig['state'].fillna("") + " " + sig['zip_code'].fillna("")

sig_map = CompanyMap(
    target_data=sig,
    name_cols=['signatory_name'],
    addr_col='ADDRESS',
    ref_name='Apprentice'
)

joblib.dump(sig_map, 'data/out/ApprenticeMap.joblib')

# %% [markdown]
# ## NYC Awarded Contracts

# %%
nyc = pd.read_csv('data/processed/Cleaned_NYC_Awarded_Contracts.csv')
nyc

# %%
prime_cols = [c for c in nyc.columns if 'prime' in c.lower()]
sub_cols = [c for c in nyc.columns if 'sub' in c.lower()]

nyc.loc[nyc['Vendor Record Type']=='Prime Vendor',sub_cols] = ''
nyc.loc[nyc['Vendor Record Type']=='Sub Vendor',prime_cols] = ''

nyc = nyc.fillna('').drop_duplicates()
nyc['ADDRESS'] = ''

nyc_map = CompanyMap(
    target_data=nyc,
    name_cols=['Prime Vendor','Sub Vendor'],
    addr_col='ADDRESS',
    ref_name='NYC Contracts'
)

joblib.dump(nyc_map, 'data/out/NYCMap.joblib')

# %% [markdown]
# ## Wage Theft

# %%
theft = pd.read_csv('data/processed/cleaned_construction_nywagetheft.csv')
theft

# %%
theft['ADDRESS'] = theft['city'].fillna("") + " " + theft['zip_code'].fillna("")

theft_map = CompanyMap(
    target_data=theft,
    name_cols=['company_name'],
    addr_col='ADDRESS',
    ref_name='Wage Theft'
)

joblib.dump(theft_map, 'data/out/TheftMap.joblib')

# %%
final = OneMapToRuleThemAll(
    [reg_map, debar_map, sig_map, nyc_map, theft_map],
)

joblib.dump(final, 'data/out/FinalMap.joblib')


