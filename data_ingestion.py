import os
import pandas as pd
import numpy as np

def inspect_file(file_path):
    print("=" * 60)
    print(f"File: {os.path.basename(file_path)}")
    print("=" * 60)
    
    # Load dataset
    df = pd.read_csv(file_path)
    
    # Shape
    print(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")
    print("\nData Types:")
    print(df.dtypes)
    print("\nHead (First 3 rows):")
    print(df.head(3))
    
    # Basic anomaly detection
    anomalies = []
    
    # 1. Null counts
    nulls = df.isnull().sum()
    null_cols = nulls[nulls > 0]
    if not null_cols.empty:
        anomalies.append(f"Missing values found: {null_cols.to_dict()}")
        
    # 2. Duplicates
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        anomalies.append(f"Duplicate rows found: {dup_count}")
        
    # 3. Numeric range check (negative values check in positive-only fields)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        # Don't check coordinates or transaction changes/returns which can be negative
        if any(keyword in col.lower() for keyword in ["return", "change", "diff", "latitude", "longitude"]):
            continue
        neg_count = (df[col] < 0).sum()
        if neg_count > 0:
            anomalies.append(f"Negative values ({neg_count}) found in column '{col}'")
            
    if anomalies:
        print("\nAnomalies Detected:")
        for anomaly in anomalies:
            print(f"  - {anomaly}")
    else:
        print("\nAnomalies Detected: None")
        
    print("\n" + "-" * 60 + "\n")
    return df, anomalies

def main():
    data_dir = os.path.join("data", "raw")
    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)
    
    # List of files in order
    files = [
        "01_fund_master.csv",
        "02_nav_history.csv",
        "03_aum_by_fund_house.csv",
        "04_monthly_sip_inflows.csv",
        "05_category_inflows.csv",
        "06_industry_folio_count.csv",
        "07_scheme_performance.csv",
        "08_investor_transactions.csv",
        "09_portfolio_holdings.csv",
        "10_benchmark_indices.csv"
    ]
    
    loaded_data = {}
    all_anomalies = {}
    
    print("### STEP 1: LOADING AND INSPECTING DATASETS ###\n")
    for file_name in files:
        file_path = os.path.join(data_dir, file_name)
        if os.path.exists(file_path):
            df, anomalies = inspect_file(file_path)
            loaded_data[file_name] = df
            all_anomalies[file_name] = anomalies
        else:
            print(f"Warning: File {file_name} not found in {data_dir}\n")
            
    # Step 2: Explore Fund Master
    print("### STEP 2: EXPLORING FUND MASTER ###\n")
    if "01_fund_master.csv" in loaded_data:
        fm_df = loaded_data["01_fund_master.csv"]
        
        unique_houses = fm_df["fund_house"].dropna().unique()
        unique_categories = fm_df["category"].dropna().unique()
        unique_subcats = fm_df["sub_category"].dropna().unique()
        unique_risks = fm_df["risk_category"].dropna().unique() if "risk_category" in fm_df.columns else fm_df["risk_grade"].dropna().unique()
        
        print(f"Unique Fund Houses ({len(unique_houses)}):")
        print(", ".join(sorted(unique_houses)))
        print(f"\nUnique Categories ({len(unique_categories)}):")
        print(", ".join(sorted(unique_categories)))
        print(f"\nUnique Sub-Categories ({len(unique_subcats)}):")
        print(", ".join(sorted(unique_subcats)))
        print(f"\nUnique Risk Categories ({len(unique_risks)}):")
        print(", ".join(sorted(unique_risks)))
        
        # AMFI Code Structure
        print("\nAMFI Code Structure Analysis:")
        amfi_codes = fm_df["amfi_code"].dropna()
        print(f"Total AMFI Codes in Master: {len(amfi_codes)}")
        print(f"Data type: {amfi_codes.dtype}")
        print(f"Min Code: {amfi_codes.min()}, Max Code: {amfi_codes.max()}")
        # Check digit length
        code_lens = amfi_codes.astype(str).str.len().unique()
        print(f"Unique AMFI Code Digit Lengths: {code_lens}")
    else:
        print("Fund master not loaded. Skipping exploration.\n")
        
    # Step 3: Validate AMFI Codes
    print("\n### STEP 3: VALIDATING AMFI CODES ###\n")
    validation_summary = ""
    if "01_fund_master.csv" in loaded_data and "02_nav_history.csv" in loaded_data:
        fm_df = loaded_data["01_fund_master.csv"]
        nav_df = loaded_data["02_nav_history.csv"]
        
        fm_codes = set(fm_df["amfi_code"].dropna().unique())
        nav_codes = set(nav_df["amfi_code"].dropna().unique())
        
        missing_in_nav = fm_codes - nav_codes
        extra_in_nav = nav_codes - fm_codes
        
        validation_summary += "## AMFI Code Validation Results\n\n"
        validation_summary += f"- Unique AMFI codes in fund_master: **{len(fm_codes)}**\n"
        validation_summary += f"- Unique AMFI codes in nav_history: **{len(nav_codes)}**\n"
        
        if len(missing_in_nav) == 0:
            validation_summary += "- **PASS**: Every AMFI code in fund_master exists in nav_history.\n"
        else:
            validation_summary += f"- **FAIL**: {len(missing_in_nav)} codes in fund_master are missing from nav_history:\n"
            validation_summary += f"  `{sorted(list(missing_in_nav))}`\n"
            
        if len(extra_in_nav) > 0:
            validation_summary += f"- **NOTE**: {len(extra_in_nav)} codes exist in nav_history but not in fund_master:\n"
            validation_summary += f"  `{sorted(list(extra_in_nav))}`\n"
        else:
            validation_summary += "- **NOTE**: No extra AMFI codes exist in nav_history.\n"
            
        print(validation_summary)
    else:
        validation_summary = "Missing fund_master or nav_history to validate codes.\n"
        print(validation_summary)
        
    # Write Data Quality Summary Report
    print("### STEP 4: GENERATING DATA QUALITY SUMMARY ###\n")
    dq_file = os.path.join(reports_dir, "data_quality_summary.md")
    
    dq_report = "# Data Quality Summary Report (Day 1 Ingestion)\n\n"
    dq_report += f"Generated automatically after inspecting {len(loaded_data)} datasets.\n\n"
    
    dq_report += "## Dataset Health Matrix\n\n"
    dq_report += "| Dataset Name | Rows | Columns | Nulls | Duplicates | Anomalies Status |\n"
    dq_report += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
    
    for file_name in files:
        if file_name in loaded_data:
            df = loaded_data[file_name]
            nulls_cnt = df.isnull().sum().sum()
            dups_cnt = df.duplicated().sum()
            status = "⚠️ Issue(s) found" if all_anomalies[file_name] else "✅ Healthy"
            dq_report += f"| {file_name} | {df.shape[0]} | {df.shape[1]} | {nulls_cnt} | {dups_cnt} | {status} |\n"
        else:
            dq_report += f"| {file_name} | Missing | Missing | - | - | ❌ Not Found |\n"
            
    dq_report += "\n## Detailed Anomalies By File\n\n"
    for file_name, anomalies in all_anomalies.items():
        if anomalies:
            dq_report += f"### {file_name}\n"
            for anomaly in anomalies:
                dq_report += f"- {anomaly}\n"
            dq_report += "\n"
            
    dq_report += f"\n{validation_summary}"
    
    with open(dq_file, "w", encoding="utf-8") as f:
        f.write(dq_report)
    print(f"Data quality summary report saved to: {dq_file}\n")

if __name__ == "__main__":
    main()
