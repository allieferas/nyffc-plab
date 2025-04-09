## Data Sources

NYS Debarments:
    * in: data/raw/NYSDOL_debarment_02_19_2025.pdf
    * process: notebooks/debarment.ipynb
    * out: data/processed/NYSDOL_debarment_02_19_2025.csv

Contractor Registry:
    * in: data/raw/Contractor_Registry_Certificate_20250215.csv
    * process: notebooks/ContractorRegistry.ipynb
    * out: data/processed/cleaned_contractors.csv

NYC Awarded Contracts:
    * in: data/raw/NYC_Awarded_Contracts.csv
    * process: notebooks/Awarded_NYC_Contracts.ipynb
    * out: data/processed/Cleaned_NYC_Awarded_Contracts.csv

Wage Theft:
    * in: -
    * process: notebooks/Construction_NYWageTheft.ipynb
    * out: data/processed/cleaned_construction_nywagetheft.csv

Construction Apprentices:
    * in: -
    * process: notebooks/Construction_Apprentice.ipynb
    * out: data/processed/cleaned_construction_apprentice.csv #check, file doesn't match

USDOL Wage Compliance:
    * in: -
    * process: notebooks/usdol_wage.ipynb
    * out: data/processed/usdol_wage_construction.csv