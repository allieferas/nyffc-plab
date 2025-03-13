import tkinter as tk
from tkinter import messagebox, scrolledtext
import pandas as pd
import os
from mapping import CompanyMap, norm_string
import joblib



# Load Data
mapper = joblib.load("data/out/FinalMap.joblib")


# Business Search Function
def search_business():
    search_name = norm_string(entry_name.get())
    search_addr = norm_string(entry_addr.get())
    if not search_name:
        messagebox.showerror("Error", "Please enter a Business Name!")
        return

    # get matches
    matches = mapper.get_matches(names=[search_name], address=search_addr)

    if len(matches)==0:
        messagebox.showinfo("No Match", f"No business found for '{search_name}'.")
        return
    """
    # Ensure "Exact Match" Retrieves Correct Contracts
    if search_term_cleaned == "Exact Match":
        contracts = df_contracts[
            (df_contracts["Prime Vendor"] == df_contracts["Prime Vendor Match"]) |
            (df_contracts["Sub Vendor"] == df_contracts["Sub Vendor Match"])
        ]
    else:
        contracts = df_contracts[
            (df_contracts["Prime Vendor Match"].str.contains(search_term_cleaned, na=False, case=False)) | 
            (df_contracts["Sub Vendor Match"].str.contains(search_term_cleaned, na=False, case=False))
        ]

    # Build Business Profile Display
    profile_text = f"\n📌 Business Profile for {search_term_cleaned}\n" + "-" * 40
    
    for record in business_data:
        profile_text += f
🏢 Address: {record.get('Address', 'N/A')}
📍 City: {record.get('City', 'N/A')}, {record.get('State', 'N/A')} {record.get('Zip Code', 'N/A')}
☎️ Phone: {record.get('Phone', 'N/A')}
🏢 MWBE Owned: {record.get('Business is MWBE Owned', 'N/A')}
🚫 Debarment Status: {record.get('Business has been debarred', 'N/A')}
🏗️ Apprenticeship Program: {record.get('Business is associated with an apprenticeship program', 'N/A')}
--------------------------------------


    # Build Contract Details
    contract_text = "\n📑 Contracts Associated with This Business:\n" if not contracts.empty else "❌ No contracts found for this business."

    for _, row in contracts.iterrows():
        contract_text += f"\n🔹 Contract ID: {row['Prime Contract ID']} | ${row['Prime Contract Current Amount']}\n"
        contract_text += f"   🔹 Contracting Agency: {row['Prime Contracting Agency']}\n"
        contract_text += f"   🔹 Start: {row['Prime Contract Start Date']} - End: {row['Prime Contract End Date']}\n"
        contract_text += "-" * 50
    """
    # Display Results in GUI
    profile_output.delete(1.0, tk.END)
    if len(matches)>0:
        for m,d in matches.items():
            cols = mapper.mappers[m].name_cols + [mapper.mappers[m].addr_col]
            profile_output.insert(tk.END, f"{m}\n{d[cols]}\n\n")

# GUI Setup
root = tk.Tk()
root.title("Contractor Profile Lookup")
root.geometry("750x700")

# Search Box
tk.Label(root, text="Enter Business Name:", font=("Arial", 12)).pack(pady=5)
entry_name = tk.Entry(root, font=("Arial", 12), width=40)
entry_name.pack(pady=5)
entry_addr = tk.Entry(root, font=("Arial", 12), width=40)
entry_addr.pack(pady=5)

# Search Button
tk.Button(root, text="Search", font=("Arial", 12), command=search_business).pack(pady=10)

# Profile Output (Scrollable)
profile_output = scrolledtext.ScrolledText(root, width=80, height=25, font=("Arial", 10))
profile_output.pack(pady=10, padx=10)

# Run the App
root.mainloop()
