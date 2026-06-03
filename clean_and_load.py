import os
import sqlite3
import pandas as pd
import numpy as np

def clean_data():
    print("### STARTING DATA CLEANING PHASE ###")
    raw_dir = os.path.join("data", "raw")
    processed_dir = os.path.join("data", "processed")
    os.makedirs(processed_dir, exist_ok=True)
    
    # 1. Clean fund_master.csv
    print("Cleaning 01_fund_master.csv...")
    df_fund = pd.read_csv(os.path.join(raw_dir, "01_fund_master.csv"))
    # Clean string columns
    for col in df_fund.select_dtypes(include=['object']).columns:
        df_fund[col] = df_fund[col].astype(str).str.strip()
    # Format launch_date
    df_fund['launch_date'] = pd.to_datetime(df_fund['launch_date']).dt.strftime('%Y-%m-%d')
    # Validate numeric columns
    numeric_cols = ['expense_ratio_pct', 'exit_load_pct', 'min_sip_amount', 'min_lumpsum_amount']
    for col in numeric_cols:
        df_fund[col] = pd.to_numeric(df_fund[col], errors='coerce')
    df_fund.to_csv(os.path.join(processed_dir, "clean_fund_master.csv"), index=False)
    print(f"Saved clean_fund_master.csv with {len(df_fund)} rows.")

    # 2. Clean nav_history.csv
    print("Cleaning 02_nav_history.csv...")
    df_nav = pd.read_csv(os.path.join(raw_dir, "02_nav_history.csv"))
    df_nav['date'] = pd.to_datetime(df_nav['date'])
    df_nav['nav'] = pd.to_numeric(df_nav['nav'], errors='coerce')
    
    # Sort and remove duplicates
    df_nav = df_nav.sort_values(by=['amfi_code', 'date']).drop_duplicates(subset=['amfi_code', 'date'])
    
    # Forward-fill missing NAV (holidays) per fund
    cleaned_nav_dfs = []
    # Find global date range (business days freq='B')
    global_min_date = df_nav['date'].min()
    global_max_date = df_nav['date'].max()
    b_days = pd.date_range(start=global_min_date, end=global_max_date, freq='B')
    
    for amfi_code, group in df_nav.groupby('amfi_code'):
        # Reindex to full business days range to handle weekday holidays
        group = group.set_index('date').reindex(b_days)
        group.index.name = 'date'
        
        # Fill missing values
        group['amfi_code'] = amfi_code
        group['nav'] = group['nav'].ffill().bfill()
        
        # Calculate daily_return: (NAV_t - NAV_t-1) / NAV_t-1
        group['daily_return'] = group['nav'].pct_change()
        
        group = group.reset_index()
        cleaned_nav_dfs.append(group)
        
    df_nav_clean = pd.concat(cleaned_nav_dfs, ignore_index=True)
    
    # Validate NAV > 0
    df_nav_clean = df_nav_clean[df_nav_clean['nav'] > 0]
    
    # Format date back to string
    df_nav_clean['date'] = df_nav_clean['date'].dt.strftime('%Y-%m-%d')
    # Force correct type
    df_nav_clean['amfi_code'] = df_nav_clean['amfi_code'].astype(int)
    
    df_nav_clean.to_csv(os.path.join(processed_dir, "clean_nav.csv"), index=False)
    print(f"Saved clean_nav.csv with {len(df_nav_clean)} rows.")

    # 3. Clean aum_by_fund_house.csv
    print("Cleaning 03_aum_by_fund_house.csv...")
    df_aum = pd.read_csv(os.path.join(raw_dir, "03_aum_by_fund_house.csv"))
    df_aum['fund_house'] = df_aum['fund_house'].astype(str).str.strip()
    df_aum['date'] = pd.to_datetime(df_aum['date']).dt.strftime('%Y-%m-%d')
    df_aum['aum_lakh_crore'] = pd.to_numeric(df_aum['aum_lakh_crore'], errors='coerce')
    df_aum['aum_crore'] = pd.to_numeric(df_aum['aum_crore'], errors='coerce')
    df_aum['num_schemes'] = pd.to_numeric(df_aum['num_schemes'], errors='coerce').astype(int)
    df_aum.to_csv(os.path.join(processed_dir, "clean_aum.csv"), index=False)
    print(f"Saved clean_aum.csv with {len(df_aum)} rows.")

    # 4. Clean monthly_sip_inflows.csv
    print("Cleaning 04_monthly_sip_inflows.csv...")
    df_sip = pd.read_csv(os.path.join(raw_dir, "04_monthly_sip_inflows.csv"))
    # Month is in YYYY-MM format, let's keep it clean
    df_sip['month'] = df_sip['month'].astype(str).str.strip()
    # Check numeric columns
    numeric_sip_cols = ['sip_inflow_crore', 'active_sip_accounts_crore', 'new_sip_accounts_lakh', 'sip_aum_lakh_crore', 'yoy_growth_pct']
    for col in numeric_sip_cols:
        df_sip[col] = pd.to_numeric(df_sip[col], errors='coerce')
    df_sip.to_csv(os.path.join(processed_dir, "clean_sip_inflows.csv"), index=False)
    print(f"Saved clean_sip_inflows.csv with {len(df_sip)} rows.")

    # 5. Clean category_inflows.csv
    print("Cleaning 05_category_inflows.csv...")
    df_cat = pd.read_csv(os.path.join(raw_dir, "05_category_inflows.csv"))
    df_cat['month'] = df_cat['month'].astype(str).str.strip()
    df_cat['category'] = df_cat['category'].astype(str).str.strip()
    df_cat['net_inflow_crore'] = pd.to_numeric(df_cat['net_inflow_crore'], errors='coerce')
    df_cat.to_csv(os.path.join(processed_dir, "clean_category_inflows.csv"), index=False)
    print(f"Saved clean_category_inflows.csv with {len(df_cat)} rows.")

    # 6. Clean industry_folio_count.csv
    print("Cleaning 06_industry_folio_count.csv...")
    df_folio = pd.read_csv(os.path.join(raw_dir, "06_industry_folio_count.csv"))
    df_folio['month'] = df_folio['month'].astype(str).str.strip()
    for col in df_folio.columns:
        if col != 'month':
            df_folio[col] = pd.to_numeric(df_folio[col], errors='coerce')
    df_folio.to_csv(os.path.join(processed_dir, "clean_folio_count.csv"), index=False)
    print(f"Saved clean_folio_count.csv with {len(df_folio)} rows.")

    # 7. Clean scheme_performance.csv
    print("Cleaning 07_scheme_performance.csv...")
    df_perf = pd.read_csv(os.path.join(raw_dir, "07_scheme_performance.csv"))
    # Standardize string fields
    df_perf['scheme_name'] = df_perf['scheme_name'].astype(str).str.strip()
    df_perf['fund_house'] = df_perf['fund_house'].astype(str).str.strip()
    df_perf['category'] = df_perf['category'].astype(str).str.strip()
    df_perf['plan'] = df_perf['plan'].astype(str).str.strip()
    df_perf['risk_grade'] = df_perf['risk_grade'].astype(str).str.strip()
    
    # Cast return columns & metrics to numeric
    numeric_perf_cols = [
        'return_1yr_pct', 'return_3yr_pct', 'return_5yr_pct', 'benchmark_3yr_pct',
        'alpha', 'beta', 'sharpe_ratio', 'sortino_ratio', 'std_dev_ann_pct',
        'max_drawdown_pct', 'aum_crore', 'expense_ratio_pct'
    ]
    for col in numeric_perf_cols:
        df_perf[col] = pd.to_numeric(df_perf[col], errors='coerce')
        
    df_perf['morningstar_rating'] = pd.to_numeric(df_perf['morningstar_rating'], errors='coerce').fillna(0).astype(int)
    
    # Flag negative Sharpe ratios
    df_perf['is_negative_sharpe'] = (df_perf['sharpe_ratio'] < 0).astype(int)
    
    # Check expense_ratio range (0.1% to 2.5%)
    outside_range = df_perf[(df_perf['expense_ratio_pct'] < 0.1) | (df_perf['expense_ratio_pct'] > 2.5)]
    if len(outside_range) > 0:
        print(f"  Warning: {len(outside_range)} schemes have expense ratios outside [0.1%, 2.5%]:")
        print(outside_range[['scheme_name', 'expense_ratio_pct']])
        
    df_perf.to_csv(os.path.join(processed_dir, "clean_performance.csv"), index=False)
    print(f"Saved clean_performance.csv with {len(df_perf)} rows.")

    # 8. Clean investor_transactions.csv
    print("Cleaning 08_investor_transactions.csv...")
    df_tx = pd.read_csv(os.path.join(raw_dir, "08_investor_transactions.csv"))
    # Standardise transaction_type (SIP/Lumpsum/Redemption)
    df_tx['transaction_type'] = df_tx['transaction_type'].astype(str).str.strip()
    # Map any variants to match exact casing/naming
    type_mapping = {
        'sip': 'SIP', 'Sip': 'SIP', 'SIP': 'SIP',
        'lumpsum': 'Lumpsum', 'Lumpsum': 'Lumpsum', 'LUMPSUM': 'Lumpsum',
        'redemption': 'Redemption', 'Redemption': 'Redemption', 'REDEMPTION': 'Redemption'
    }
    df_tx['transaction_type'] = df_tx['transaction_type'].map(type_mapping).fillna(df_tx['transaction_type'])
    
    # Validate amount > 0
    df_tx = df_tx[df_tx['amount_inr'] > 0]
    
    # Validate KYC status values
    df_tx['kyc_status'] = df_tx['kyc_status'].astype(str).str.strip()
    kyc_mapping = {
        'verified': 'Verified', 'Verified': 'Verified', 'VERIFIED': 'Verified',
        'pending': 'Pending', 'Pending': 'Pending', 'PENDING': 'Pending'
    }
    df_tx['kyc_status'] = df_tx['kyc_status'].map(kyc_mapping).fillna(df_tx['kyc_status'])
    
    # Fix date formats
    df_tx['transaction_date'] = pd.to_datetime(df_tx['transaction_date']).dt.strftime('%Y-%m-%d')
    
    # Clean other string columns
    for col in ['investor_id', 'state', 'city', 'city_tier', 'age_group', 'gender', 'payment_mode']:
        df_tx[col] = df_tx[col].astype(str).str.strip()
        
    df_tx['annual_income_lakh'] = pd.to_numeric(df_tx['annual_income_lakh'], errors='coerce')
    
    df_tx.to_csv(os.path.join(processed_dir, "clean_transactions.csv"), index=False)
    print(f"Saved clean_transactions.csv with {len(df_tx)} rows.")

    # 9. Clean portfolio_holdings.csv
    print("Cleaning 09_portfolio_holdings.csv...")
    df_holdings = pd.read_csv(os.path.join(raw_dir, "09_portfolio_holdings.csv"))
    for col in ['stock_symbol', 'stock_name', 'sector']:
        df_holdings[col] = df_holdings[col].astype(str).str.strip()
    df_holdings['weight_pct'] = pd.to_numeric(df_holdings['weight_pct'], errors='coerce')
    df_holdings['market_value_cr'] = pd.to_numeric(df_holdings['market_value_cr'], errors='coerce')
    df_holdings['current_price_inr'] = pd.to_numeric(df_holdings['current_price_inr'], errors='coerce')
    df_holdings['portfolio_date'] = pd.to_datetime(df_holdings['portfolio_date']).dt.strftime('%Y-%m-%d')
    df_holdings.to_csv(os.path.join(processed_dir, "clean_portfolio_holdings.csv"), index=False)
    print(f"Saved clean_portfolio_holdings.csv with {len(df_holdings)} rows.")

    # 10. Clean benchmark_indices.csv
    print("Cleaning 10_benchmark_indices.csv...")
    df_bench = pd.read_csv(os.path.join(raw_dir, "10_benchmark_indices.csv"))
    df_bench['index_name'] = df_bench['index_name'].astype(str).str.strip()
    df_bench['date'] = pd.to_datetime(df_bench['date']).dt.strftime('%Y-%m-%d')
    df_bench['close_value'] = pd.to_numeric(df_bench['close_value'], errors='coerce')
    df_bench.to_csv(os.path.join(processed_dir, "clean_benchmark_indices.csv"), index=False)
    print(f"Saved clean_benchmark_indices.csv with {len(df_bench)} rows.")
    
    print("### DATA CLEANING PHASE COMPLETE ###\n")

def load_database():
    print("### STARTING DATABASE LOADING PHASE ###")
    db_file = "bluestock_mf.db"
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"Removed existing database file: {db_file}")
        
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # 1. Execute schema.sql to create tables
    print("Executing schema.sql DDL script...")
    with open(os.path.join("sql", "schema.sql"), "r", encoding="utf-8") as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)
    conn.commit()
    print("Database tables created successfully.")
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # 2. Load cleaned data into database in dependency order
    processed_dir = os.path.join("data", "processed")
    
    # Map tables to files in correct dependency order
    load_mappings = [
        ("dim_fund", "clean_fund_master.csv"),
        ("fact_nav", "clean_nav.csv"),
        ("fact_performance", "clean_performance.csv"),
        ("fact_transactions", "clean_transactions.csv"),
        ("fact_portfolio_holdings", "clean_portfolio_holdings.csv"),
        ("fact_benchmark_indices", "clean_benchmark_indices.csv"),
        ("fact_sip_inflows", "clean_sip_inflows.csv"),
        ("fact_category_inflows", "clean_category_inflows.csv"),
        ("dim_aum_fund_house", "clean_aum.csv"),
        ("dim_industry_folio", "clean_folio_count.csv")
    ]
    
    for table_name, file_name in load_mappings:
        file_path = os.path.join(processed_dir, file_name)
        df = pd.read_csv(file_path)
        print(f"Loading {len(df)} rows into table '{table_name}'...")
        
        # Replace empty values / NaN with None for SQLite NULL compatibility
        df = df.replace({np.nan: None})
        
        # Rename columns to match SQLite schema where necessary
        if table_name == "fact_nav":
            df = df.rename(columns={"date": "nav_date"})

        # Special handling for auto-incrementing transaction_id in fact_transactions
        # If the file does not have it, do not pass transaction_id so SQLite handles auto-increment
        if table_name == "fact_transactions" and "transaction_id" not in df.columns:
            # Let SQLite auto-generate it
            pass
            
        # Write to SQL
        df.to_sql(table_name, conn, if_exists="append", index=False)
        conn.commit()
        
    # Check row counts in db
    print("\nDatabase Row Counts Summary:")
    for table_name, _ in load_mappings:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        cnt = cursor.fetchone()[0]
        print(f"  - Table '{table_name}': {cnt} rows")
        
    conn.close()
    print("### DATABASE LOADING PHASE COMPLETE ###")

if __name__ == "__main__":
    clean_data()
    load_database()
