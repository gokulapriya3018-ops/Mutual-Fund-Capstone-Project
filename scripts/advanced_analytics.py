import sqlite3
import pandas as pd
import numpy as np

def run_advanced_analytics():
    print("### STARTING ADVANCED RISK & STRATEGY ANALYTICS ###")
    conn = sqlite3.connect("bluestock_mf.db")
    cursor = conn.cursor()
    
    # -------------------------------------------------------------
    # 1. Value at Risk (VaR) and Conditional VaR (CVaR)
    # -------------------------------------------------------------
    print("Calculating VaR and CVaR for funds...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fact_advanced_risk (
            amfi_code TEXT PRIMARY KEY,
            var_95_pct REAL,
            cvar_95_pct REAL,
            FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
        );
    """)
    conn.commit()
    
    # Load all distinct amfi_codes
    cursor.execute("SELECT amfi_code FROM dim_fund;")
    codes = [row[0] for row in cursor.fetchall()]
    
    risk_records = []
    for code in codes:
        # Load daily returns
        returns_df = pd.read_sql_query(f"""
            SELECT daily_return FROM fact_nav 
            WHERE amfi_code = '{code}' AND daily_return IS NOT NULL;
        """, conn)
        
        if len(returns_df) > 10:
            ret = returns_df['daily_return'].values * 100 # Convert to percent
            
            # 95% Daily VaR: 5th percentile of daily returns
            var_95 = np.percentile(ret, 5)
            # CVaR: average of returns worse than VaR
            cvar_95 = ret[ret <= var_95].mean()
            
            risk_records.append((code, float(var_95), float(cvar_95)))
            
    cursor.executemany("""
        INSERT OR REPLACE INTO fact_advanced_risk (amfi_code, var_95_pct, cvar_95_pct)
        VALUES (?, ?, ?);
    """, risk_records)
    conn.commit()
    print(f"Calculated VaR & CVaR for {len(risk_records)} funds and saved to 'fact_advanced_risk'.")
    
    # -------------------------------------------------------------
    # 2. Rolling Sharpe Ratio (90 business days window)
    # -------------------------------------------------------------
    print("Calculating 90-day Rolling Sharpe ratios...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fact_rolling_sharpe (
            amfi_code TEXT,
            nav_date DATE,
            rolling_sharpe REAL,
            PRIMARY KEY (amfi_code, nav_date),
            FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
        );
    """)
    conn.commit()
    
    # Let's calculate rolling Sharpe for the top 10 funds by AUM to keep database compact
    top_10_funds_query = "SELECT amfi_code FROM fact_performance ORDER BY aum_crore DESC LIMIT 10;"
    cursor.execute(top_10_funds_query)
    top_10_codes = [row[0] for row in cursor.fetchall()]
    
    rolling_sharpe_records = []
    rf_daily = 0.06 / 252
    
    for code in top_10_codes:
        nav_df = pd.read_sql_query(f"""
            SELECT nav_date, nav, daily_return 
            FROM fact_nav 
            WHERE amfi_code = '{code}' 
            ORDER BY nav_date;
        """, conn)
        
        if len(nav_df) > 90:
            nav_df['nav_date'] = pd.to_datetime(nav_df['nav_date'])
            # Rolling window calculations
            rolling_mean = nav_df['daily_return'].rolling(window=90).mean()
            rolling_std = nav_df['daily_return'].rolling(window=90).std()
            
            # Annualized rolling return and std dev
            # Ann Sharpe = (Mean * 252 - 0.06) / (Std * sqrt(252))
            # Let's make sure std > 0 to avoid division by zero
            rolling_sharpe = (rolling_mean * 252 - 0.06) / (rolling_std * np.sqrt(252))
            
            nav_df['rolling_sharpe'] = rolling_sharpe
            nav_df = nav_df.dropna(subset=['rolling_sharpe'])
            
            for _, row in nav_df.iterrows():
                date_str = row['nav_date'].strftime('%Y-%m-%d')
                rolling_sharpe_records.append((code, date_str, float(row['rolling_sharpe'])))
                
    cursor.executemany("""
        INSERT OR REPLACE INTO fact_rolling_sharpe (amfi_code, nav_date, rolling_sharpe)
        VALUES (?, ?, ?);
    """, rolling_sharpe_records)
    conn.commit()
    print(f"Calculated 90-day rolling Sharpe ratios for top 10 funds ({len(rolling_sharpe_records)} records).")
    
    # -------------------------------------------------------------
    # 3. Cohort Analysis of Investors
    # -------------------------------------------------------------
    print("Performing Cohort Analysis on transactions...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fact_cohort_metrics (
            cohort_quarter TEXT,
            cohort_size INTEGER,
            activity_quarter TEXT,
            quarter_index INTEGER,
            active_investors INTEGER,
            retention_pct REAL,
            total_amount_inr REAL,
            avg_amount_inr REAL,
            PRIMARY KEY (cohort_quarter, activity_quarter)
        );
    """)
    conn.commit()
    
    # Load transactions
    tx_df = pd.read_sql_query("SELECT investor_id, transaction_date, amount_inr FROM fact_transactions;", conn)
    tx_df['transaction_date'] = pd.to_datetime(tx_df['transaction_date'])
    tx_df['quarter'] = tx_df['transaction_date'].dt.to_period('Q').astype(str)
    
    # Find joining date (min date) for each investor
    joining_dates = tx_df.groupby('investor_id')['transaction_date'].min().reset_index()
    joining_dates = joining_dates.rename(columns={'transaction_date': 'joining_date'})
    joining_dates['cohort_quarter'] = joining_dates['joining_date'].dt.to_period('Q').astype(str)
    
    # Merge back to transactions
    tx_merged = pd.merge(tx_df, joining_dates[['investor_id', 'cohort_quarter']], on='investor_id', how='left')
    
    # Determine the index of the activity quarter relative to cohort quarter
    cohort_sizes = joining_dates.groupby('cohort_quarter')['investor_id'].nunique().reset_index()
    cohort_sizes = cohort_sizes.rename(columns={'investor_id': 'cohort_size'})
    
    cohort_activity = tx_merged.groupby(['cohort_quarter', 'quarter']).agg(
        active_investors=('investor_id', 'nunique'),
        total_amount=('amount_inr', 'sum'),
        avg_amount=('amount_inr', 'mean')
    ).reset_index()
    
    cohort_activity = pd.merge(cohort_activity, cohort_sizes, on='cohort_quarter', how='left')
    
    # Helper to calculate distance in quarters
    def diff_quarters(q1, q2):
        # Format is YYYY-Q1
        y1, qr1 = int(q1[:4]), int(q1[-1])
        y2, qr2 = int(q2[:4]), int(q2[-1])
        return (y2 - y1) * 4 + (qr2 - qr1)
        
    cohort_activity['quarter_index'] = cohort_activity.apply(lambda r: diff_quarters(r['cohort_quarter'], r['quarter']), axis=1)
    
    # Only keep future/present quarters
    cohort_activity = cohort_activity[cohort_activity['quarter_index'] >= 0]
    cohort_activity['retention_pct'] = (cohort_activity['active_investors'] / cohort_activity['cohort_size']) * 100
    
    cohort_records = []
    for _, row in cohort_activity.iterrows():
        cohort_records.append((
            row['cohort_quarter'],
            int(row['cohort_size']),
            row['quarter'],
            int(row['quarter_index']),
            int(row['active_investors']),
            float(row['retention_pct']),
            float(row['total_amount']),
            float(row['avg_amount'])
        ))
        
    cursor.executemany("""
        INSERT OR REPLACE INTO fact_cohort_metrics 
        (cohort_quarter, cohort_size, activity_quarter, quarter_index, active_investors, retention_pct, total_amount_inr, avg_amount_inr)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, cohort_records)
    conn.commit()
    print(f"Cohort metrics calculated and loaded ({len(cohort_records)} records).")
    
    # -------------------------------------------------------------
    # 4. SIP Continuation Analysis
    # -------------------------------------------------------------
    print("Performing SIP Continuation Analysis...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fact_sip_continuation (
            investor_id TEXT PRIMARY KEY,
            last_transaction_date DATE,
            days_since_last_tx INTEGER,
            status TEXT
        );
    """)
    conn.commit()
    
    # Get the global max date of transaction to compare
    cursor.execute("SELECT MAX(transaction_date) FROM fact_transactions;")
    max_tx_date_str = cursor.fetchone()[0]
    max_tx_date = pd.to_datetime(max_tx_date_str)
    
    # Get latest SIP transaction for each investor
    sip_txs = pd.read_sql_query("""
        SELECT investor_id, MAX(transaction_date) as last_tx
        FROM fact_transactions
        WHERE transaction_type = 'SIP'
        GROUP BY investor_id;
    """, conn)
    
    sip_continuation_records = []
    for _, row in sip_txs.iterrows():
        inv_id = row['investor_id']
        last_date = pd.to_datetime(row['last_tx'])
        gap = (max_tx_date - last_date).days
        status = 'At Risk' if gap > 35 else 'Active'
        sip_continuation_records.append((inv_id, row['last_tx'], int(gap), status))
        
    cursor.executemany("""
        INSERT OR REPLACE INTO fact_sip_continuation (investor_id, last_transaction_date, days_since_last_tx, status)
        VALUES (?, ?, ?, ?);
    """, sip_continuation_records)
    conn.commit()
    
    # Let's count how many are active vs at risk
    cursor.execute("SELECT status, COUNT(*) FROM fact_sip_continuation GROUP BY status;")
    print("SIP continuation status:", cursor.fetchall())
    
    # -------------------------------------------------------------
    # 5. Herfindahl-Hirschman Index (HHI) for Sector Concentration Risk
    # -------------------------------------------------------------
    print("Calculating Sector Concentration Risk (HHI) for portfolios...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fact_sector_concentration (
            amfi_code TEXT PRIMARY KEY,
            scheme_name TEXT,
            hhi_index REAL,
            concentration_level TEXT,
            FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
        );
    """)
    conn.commit()
    
    # Load portfolio holdings weights grouped by fund and sector
    holdings_df = pd.read_sql_query("""
        SELECT amfi_code, sector, SUM(weight_pct) as sector_weight
        FROM fact_portfolio_holdings
        GROUP BY amfi_code, sector;
    """, conn)
    
    # Group by amfi_code to calculate HHI = sum(weight^2)
    hhi_records = []
    for amfi_code, group in holdings_df.groupby('amfi_code'):
        weights = group['sector_weight'].values
        # Normalize weights so they sum to 100 if there's any small parsing offset
        total_w = np.sum(weights)
        if total_w > 0:
            weights = (weights / total_w) * 100
            
        hhi = np.sum(weights ** 2)
        
        # Classification
        if hhi < 1500:
            level = 'Diversified'
        elif hhi <= 2500:
            level = 'Moderate Concentration'
        else:
            level = 'High Concentration'
            
        # Get scheme name
        cursor.execute("SELECT scheme_name FROM dim_fund WHERE amfi_code = ?;", (amfi_code,))
        scheme_row = cursor.fetchone()
        scheme_name = scheme_row[0] if scheme_row else "Unknown Scheme"
        
        hhi_records.append((amfi_code, scheme_name, float(hhi), level))
        
    cursor.executemany("""
        INSERT OR REPLACE INTO fact_sector_concentration (amfi_code, scheme_name, hhi_index, concentration_level)
        VALUES (?, ?, ?, ?);
    """, hhi_records)
    conn.commit()
    print(f"Calculated HHI Concentration for {len(hhi_records)} funds.")
    
    # -------------------------------------------------------------
    # 6. Fund Recommendation Engine
    # -------------------------------------------------------------
    print("Pre-building Fund Recommendations database...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fact_recommendations (
            risk_profile TEXT,
            rank INTEGER,
            amfi_code TEXT,
            scheme_name TEXT,
            category TEXT,
            sharpe_ratio REAL,
            cagr_pct REAL,
            max_drawdown_pct REAL,
            PRIMARY KEY (risk_profile, rank)
        );
    """)
    conn.commit()
    
    # Low Risk recommendations: Debt / Liquid funds with high Sharpe ratio
    low_risk_query = """
        SELECT f.amfi_code, f.scheme_name, f.category, p.sharpe_ratio, p.return_3yr_pct as cagr, p.max_drawdown_pct
        FROM dim_fund f
        JOIN fact_performance p ON f.amfi_code = p.amfi_code
        WHERE f.risk_category IN ('Low', 'Low to Moderate', 'Moderate')
           OR f.category IN ('Debt Scheme', 'Liquid Scheme')
        ORDER BY p.sharpe_ratio DESC
        LIMIT 3;
    """
    low_df = pd.read_sql_query(low_risk_query, conn)
    
    # Moderate Risk recommendations: Large Cap / Flexi Cap with high Sharpe
    mod_risk_query = """
        SELECT f.amfi_code, f.scheme_name, f.category, p.sharpe_ratio, p.return_3yr_pct as cagr, p.max_drawdown_pct
        FROM dim_fund f
        JOIN fact_performance p ON f.amfi_code = p.amfi_code
        WHERE f.risk_category IN ('Moderately High', 'High')
          AND f.sub_category IN ('Large Cap', 'Flexi Cap', 'Large & Mid Cap')
        ORDER BY p.sharpe_ratio DESC
        LIMIT 3;
    """
    mod_df = pd.read_sql_query(mod_risk_query, conn)
    
    # High Risk recommendations: Small Cap / Mid Cap with high Sharpe
    high_risk_query = """
        SELECT f.amfi_code, f.scheme_name, f.category, p.sharpe_ratio, p.return_3yr_pct as cagr, p.max_drawdown_pct
        FROM dim_fund f
        JOIN fact_performance p ON f.amfi_code = p.amfi_code
        WHERE f.risk_category = 'Very High'
           OR f.sub_category IN ('Small Cap', 'Mid Cap')
        ORDER BY p.sharpe_ratio DESC
        LIMIT 3;
    """
    high_df = pd.read_sql_query(high_risk_query, conn)
    
    reco_records = []
    for r, (_, row) in enumerate(low_df.iterrows(), 1):
        reco_records.append(('Low Risk', r, row['amfi_code'], row['scheme_name'], row['category'], float(row['sharpe_ratio']), float(row['cagr']), float(row['max_drawdown_pct'])))
    for r, (_, row) in enumerate(mod_df.iterrows(), 1):
        reco_records.append(('Moderate Risk', r, row['amfi_code'], row['scheme_name'], row['category'], float(row['sharpe_ratio']), float(row['cagr']), float(row['max_drawdown_pct'])))
    for r, (_, row) in enumerate(high_df.iterrows(), 1):
        reco_records.append(('High Risk', r, row['amfi_code'], row['scheme_name'], row['category'], float(row['sharpe_ratio']), float(row['cagr']), float(row['max_drawdown_pct'])))
        
    cursor.executemany("""
        INSERT OR REPLACE INTO fact_recommendations (risk_profile, rank, amfi_code, scheme_name, category, sharpe_ratio, cagr_pct, max_drawdown_pct)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, reco_records)
    conn.commit()
    print("Recommendation engine database pre-built successfully.")
    
    conn.close()
    print("### ADVANCED RISK & STRATEGY ANALYTICS COMPLETE ###")

if __name__ == "__main__":
    run_advanced_analytics()
