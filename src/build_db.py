from mapping import FuzzyMatch
import pandas as pd
from fuzzywuzzy import fuzz
import sqlite3 as sql

reg = pd.read_csv("data/processed/cleaned_contractors.csv") 
reg['Address 2'] = reg['Address 2'].str.replace('NOT APPLICABLE', '')
reg['ADDRESS'] = reg['Address'].fillna("") + " " + reg['Address 2'].fillna("") + " " + reg['City'].fillna("") + " " + reg['State'].fillna("") + " " + reg['Zip Code'].fillna("")
reg.rename(columns={'Business Name':'NAME1','DBA Name':'NAME2'}, inplace=True)

debar = pd.read_csv('data/processed/NYSDOL_debarment_02_19_2025.csv')
debar.rename(columns={'EMPLOYER_NAME':'NAME1','EMPLOYER_DBA':'NAME2'}, inplace=True)

sig = pd.read_csv('data/processed/cleaned_apprentice.csv')
sig['ADDRESS'] = sig['signatory_address'].fillna("") + " " + sig['city'].fillna("") + " " + sig['state'].fillna("") + " " + sig['zip_code'].fillna("")
sig.rename(columns={'signatory_name':'NAME1'}, inplace=True)

nyc = pd.read_csv('data/processed/Cleaned_NYC_Awarded_Contracts.csv')
prime_cols = [c for c in nyc.columns if 'prime' in c.lower()]
sub_cols = [c for c in nyc.columns if 'sub' in c.lower()]
nyc.loc[nyc['Vendor Record Type']=='Prime Vendor','NAME1'] = nyc.loc[nyc['Vendor Record Type']=='Prime Vendor','Prime Vendor']
nyc.loc[nyc['Vendor Record Type']=='Sub Vendor','NAME1'] = nyc.loc[nyc['Vendor Record Type']=='Sub Vendor','Sub Vendor']
nyc = nyc.fillna('').drop_duplicates()
nyc['ADDRESS'] = ''

theft = pd.read_csv('data/processed/cleaned_construction_nywagetheft.csv')
theft['ADDRESS'] = theft['city'].fillna("") + " " + theft['zip_code'].fillna("")
theft.rename(columns={'company_name':'NAME1'}, inplace=True)

usdol = pd.read_csv('data/processed/usdol_wage_construction.csv')
usdol['ADDRESS'] = usdol['street_addr_1_txt'].fillna("") + " " + usdol['cty_nm'].fillna("") + " " + usdol['st_cd'].fillna("") + " " + usdol['zip_cd'].astype(str).fillna("")

df_dict = {
    'REGISTRY': reg, 
    'DEBARMENT': debar,
    'APPRENTICE': sig,
    'NYC_AWARDS': nyc,
    'WAGE_THEFT': theft,
    'USDOL': usdol} 
match = FuzzyMatch(['NAME1','NAME2'], 'ADDRESS', threshold=95, avg_threshold=80, fuzzy_alg=fuzz.ratio)
match_df, df_dict = match.index_and_match(df_dict)

conn = sql.connect('data/out/nyffc.db')
cur = conn.cursor()

match_df.to_sql('match', conn, if_exists='replace', index=False)
match.name_df.to_sql('name', conn, if_exists='replace', index=False)

for k,v in df_dict.items():
    v.to_sql(k, conn, if_exists='replace', index=False)
    conn.commit()

conn.close()
