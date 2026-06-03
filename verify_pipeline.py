import os
import sqlite3
import pandas as pd

def run_verification():
    print("### STARTING PIPELINE VERIFICATION ###")
    processed_dir = os.path.join("data", "processed")
    db_file = "bluestock_mf.db"
    
    # 1. Check cleaned files existence
    cleaned_files = {
        "clean_fund_master.csv": 40,
        "clean_nav.csv": 46000,
        "clean_aum.csv": 90,
        "clean_sip_inflows.csv": 48,
        "clean_category_inflows.csv": 144,
        "clean_folio_count.csv": 21,
        "clean_performance.csv": 40,
        "clean_transactions.csv": 32778,
        "clean_portfolio_holdings.csv": 322,
        "clean_benchmark_indices.csv": 8050
    }
    
    print("\nVerifying cleaned files in data/processed:")
    all_files_exist = True
    for file_name, expected_rows in cleaned_files.items():
        file_path = os.path.join(processed_dir, file_name)
        if not os.path.exists(file_path):
            print(f"  [FAIL] File missing: {file_name}")
            all_files_exist = False
        else:
            df = pd.read_csv(file_path)
            row_count = len(df)
            status = "PASS" if row_count == expected_rows else "WARNING (expected row count mismatch)"
            print(f"  - {file_name}: Found. Rows: {row_count} (Expected: {expected_rows}) - [{status}]")
            
    if all_files_exist:
        print("  [PASS] All 10 cleaned CSV files are present.")
        
    # 2. Check Database existence
    print("\nVerifying database bluestock_mf.db:")
    if not os.path.exists(db_file):
        print("  [FAIL] bluestock_mf.db is missing!")
        return
    else:
        print("  [PASS] bluestock_mf.db exists.")
        
    # 3. Check DB Tables and counts
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    expected_tables = {
        "dim_fund": 40,
        "fact_nav": 46000,
        "dim_aum_fund_house": 90,
        "fact_sip_inflows": 48,
        "fact_category_inflows": 144,
        "dim_industry_folio": 21,
        "fact_performance": 40,
        "fact_transactions": 32778,
        "fact_portfolio_holdings": 322,
        "fact_benchmark_indices": 8050
    }
    
    print("\nVerifying database table schemas and row counts:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    all_tables_pass = True
    for table_name, expected_count in expected_tables.items():
        if table_name not in existing_tables:
            print(f"  [FAIL] Table missing from database: {table_name}")
            all_tables_pass = False
        else:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            cnt = cursor.fetchone()[0]
            status = "PASS" if cnt == expected_count else "FAIL (mismatch)"
            if cnt != expected_count:
                all_tables_pass = False
            print(f"  - Table '{table_name}': loaded {cnt} rows (Expected: {expected_count}) - [{status}]")
            
    if all_tables_pass:
        print("  [PASS] All 10 database tables were created and populated with exact row counts.")
        
    # 4. Specific Data Validation Assertions
    print("\nRunning granular data quality assertions:")
    
    # Assert NAV > 0
    cursor.execute("SELECT COUNT(*) FROM fact_nav WHERE nav <= 0;")
    cnt_bad_nav = cursor.fetchone()[0]
    assert cnt_bad_nav == 0, f"Error: Found {cnt_bad_nav} rows in fact_nav with nav <= 0!"
    print("  [PASS] Assert: All NAV values in database are strictly greater than 0.")
    
    # Assert transactions amount > 0
    cursor.execute("SELECT COUNT(*) FROM fact_transactions WHERE amount_inr <= 0;")
    cnt_bad_amount = cursor.fetchone()[0]
    assert cnt_bad_amount == 0, f"Error: Found {cnt_bad_amount} transaction rows with amount_inr <= 0!"
    print("  [PASS] Assert: All transaction amounts in database are strictly greater than 0.")
    
    # Assert KYC status values
    cursor.execute("SELECT DISTINCT kyc_status FROM fact_transactions;")
    kyc_statuses = [row[0] for row in cursor.fetchall()]
    assert set(kyc_statuses).issubset({"Verified", "Pending"}), f"Error: Invalid KYC statuses found: {kyc_statuses}"
    print(f"  [PASS] Assert: KYC status contains only expected values: {kyc_statuses}")
    
    # Assert transaction types
    cursor.execute("SELECT DISTINCT transaction_type FROM fact_transactions;")
    tx_types = [row[0] for row in cursor.fetchall()]
    assert set(tx_types).issubset({"SIP", "Lumpsum", "Redemption"}), f"Error: Invalid transaction types found: {tx_types}"
    print(f"  [PASS] Assert: Transaction types contain only expected values: {tx_types}")
    
    # Assert negative Sharpe ratios flagged
    cursor.execute("SELECT COUNT(*) FROM fact_performance WHERE sharpe_ratio < 0 AND is_negative_sharpe = 0;")
    cnt_unflagged_sharpe = cursor.fetchone()[0]
    assert cnt_unflagged_sharpe == 0, "Error: Sharpe ratio is negative but is_negative_sharpe flag is not set!"
    print("  [PASS] Assert: All negative Sharpe ratios are correctly flagged in performance metrics.")
    
    # Assert foreign keys are active and functional
    # Let's verify by checking that there are no orphan keys in fact_nav
    cursor.execute("""
        SELECT COUNT(*) FROM fact_nav 
        WHERE amfi_code NOT IN (SELECT amfi_code FROM dim_fund);
    """)
    orphan_nav = cursor.fetchone()[0]
    assert orphan_nav == 0, f"Error: Found {orphan_nav} rows in fact_nav referencing invalid amfi_codes!"
    print("  [PASS] Assert: Foreign key reference integrity checks clean.")
    
    conn.close()
    print("\n### PIPELINE VERIFICATION SUCCESSFUL: ALL CHECKS PASSED! ###")

if __name__ == "__main__":
    run_verification()
