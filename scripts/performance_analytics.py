import sqlite3
import pandas as pd
import numpy as np

# Risk-free rate (6.0% annual)
RF_ANNUAL = 0.06
RF_DAILY = RF_ANNUAL / 252

# Mapping from fund benchmark column to index name in fact_benchmark_indices
BENCHMARK_MAPPING = {
    'BSE 250 SmallCap TRI': 'BSE_SMALLCAP',
    'CRISIL Dynamic Gilt Index': 'CRISIL_GILT',
    'CRISIL Liquid Fund AI Index': 'CRISIL_LIQUID',
    'CRISIL Short Term Bond Index': 'CRISIL_LIQUID',  # Map to Liquid as proxy
    'NIFTY 100 TRI': 'NIFTY100',
    'NIFTY 50 TRI': 'NIFTY50',
    'NIFTY 500 TRI': 'NIFTY500',
    'NIFTY Large Midcap 250 TRI': 'NIFTY500',        # Map to Nifty 500 as proxy
    'NIFTY Midcap 150 TRI': 'NIFTY_MIDCAP150',
    'NIFTY Midcap 50 TRI': 'NIFTY_MIDCAP150'        # Map to Midcap 150 as proxy
}

def calculate_cagr(start_val, end_val, days):
    years = days / 365.25
    if years <= 0 or start_val <= 0:
        return 0
    return (end_val / start_val) ** (1 / years) - 1

def run_performance_analytics():
    print("### STARTING PERFORMANCE ANALYTICS ###")
    conn = sqlite3.connect("bluestock_mf.db")
    
    # 1. Fetch funds
    funds = pd.read_sql_query("SELECT * FROM dim_fund;", conn)
    print(f"Loaded {len(funds)} funds from dim_fund.")
    
    results = []
    
    for idx, fund in funds.iterrows():
        code = fund['amfi_code']
        name = fund['scheme_name']
        bench_name = fund['benchmark']
        expense_ratio = fund['expense_ratio_pct']
        
        # Get mapped index name
        index_name = BENCHMARK_MAPPING.get(bench_name, 'NIFTY50')
        
        # Load NAV history
        nav_df = pd.read_sql_query(f"""
            SELECT nav_date, nav 
            FROM fact_nav 
            WHERE amfi_code = '{code}' 
            ORDER BY nav_date;
        """, conn)
        
        if len(nav_df) < 10:
            print(f"  Warning: Fund {code} has insufficient NAV data.")
            continue
            
        nav_df['nav_date'] = pd.to_datetime(nav_df['nav_date'])
        
        # 2. Calculate CAGR
        start_nav = nav_df['nav'].iloc[0]
        end_nav = nav_df['nav'].iloc[-1]
        days = (nav_df['nav_date'].iloc[-1] - nav_df['nav_date'].iloc[0]).days
        cagr = calculate_cagr(start_nav, end_nav, days)
        
        # 3. Daily returns
        nav_df['daily_return'] = nav_df['nav'].pct_change()
        daily_returns = nav_df['daily_return'].dropna()
        
        # Annualized return and std dev
        mean_daily_return = daily_returns.mean()
        std_daily_return = daily_returns.std()
        
        ann_return = cagr  # Compounded annual rate is more accurate than mean_daily * 252
        ann_std = std_daily_return * np.sqrt(252)
        
        # 4. Sharpe Ratio
        sharpe = (ann_return - RF_ANNUAL) / ann_std if ann_std > 0 else 0
        
        # 5. Sortino Ratio
        # Downside standard deviation penalizing returns below RF_DAILY
        downside_diffs = daily_returns - RF_DAILY
        downside_diffs_capped = np.minimum(0, downside_diffs)
        downside_std_daily = np.sqrt(np.mean(downside_diffs_capped ** 2))
        downside_std_ann = downside_std_daily * np.sqrt(252)
        sortino = (ann_return - RF_ANNUAL) / downside_std_ann if downside_std_ann > 0 else 0
        
        # 6. Maximum Drawdown
        peaks = nav_df['nav'].cummax()
        drawdowns = (nav_df['nav'] - peaks) / peaks
        max_drawdown = drawdowns.min()
        
        # 7. Beta and Alpha
        # Fetch benchmark index closing prices
        bench_df = pd.read_sql_query(f"""
            SELECT date as nav_date, close_value 
            FROM fact_benchmark_indices 
            WHERE index_name = '{index_name}'
            ORDER BY date;
        """, conn)
        bench_df['nav_date'] = pd.to_datetime(bench_df['nav_date'])
        bench_df['index_return'] = bench_df['close_value'].pct_change()
        
        # Align NAV and Benchmark on date
        merged = pd.merge(nav_df[['nav_date', 'daily_return']], bench_df[['nav_date', 'index_return']], on='nav_date', how='inner').dropna()
        
        beta = 1.0
        alpha = 0.0
        simple_alpha = 0.0
        bench_cagr = 0.0
        
        if len(merged) > 10:
            fund_merged_ret = merged['daily_return'].values
            index_merged_ret = merged['index_return'].values
            
            # Covariance / Variance for Beta
            covariance = np.cov(fund_merged_ret, index_merged_ret)[0][1]
            idx_variance = np.var(index_merged_ret, ddof=1)
            beta = covariance / idx_variance if idx_variance > 0 else 1.0
            
            # Annualized Index Return for Alpha
            bench_start = bench_df['close_value'].iloc[0]
            bench_end = bench_df['close_value'].iloc[-1]
            bench_cagr = calculate_cagr(bench_start, bench_end, days)
            
            # CAPM Alpha: Alpha = R_p - [R_f + Beta * (R_m - R_f)]
            alpha = ann_return - (RF_ANNUAL + beta * (bench_cagr - RF_ANNUAL))
            simple_alpha = ann_return - bench_cagr
            
        results.append({
            'amfi_code': code,
            'scheme_name': name,
            'fund_house': fund['fund_house'],
            'category': fund['category'],
            'plan': fund['plan'],
            'cagr': cagr,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'beta': beta,
            'alpha': alpha,
            'simple_alpha': simple_alpha,
            'std_dev_ann_pct': ann_std * 100,
            'max_drawdown_pct': max_drawdown * 100,
            'benchmark_cagr': bench_cagr,
            'expense_ratio_pct': expense_ratio
        })
        
    df_results = pd.DataFrame(results)
    
    # 8. Composite Scorecard Ranking
    # Normalize inputs: 0 to 100
    def min_max_normalize(series, invert=False):
        s_min = series.min()
        s_max = series.max()
        if s_max == s_min:
            return 50.0
        if invert:
            return (s_max - series) / (s_max - s_min) * 100
        else:
            return (series - s_min) / (s_max - s_min) * 100
            
    df_results['norm_sharpe'] = min_max_normalize(df_results['sharpe_ratio'])
    df_results['norm_alpha'] = min_max_normalize(df_results['alpha'])
    df_results['norm_cagr'] = min_max_normalize(df_results['cagr'])
    # Drawdowns are negative, so more negative is worse, less negative (higher) is better
    df_results['norm_drawdown'] = min_max_normalize(df_results['max_drawdown_pct'])
    # Lower expense ratio is better, so invert normalization
    df_results['norm_expense'] = min_max_normalize(df_results['expense_ratio_pct'], invert=True)
    
    df_results['composite_score'] = (
        0.30 * df_results['norm_sharpe'] +
        0.25 * df_results['norm_alpha'] +
        0.20 * df_results['norm_cagr'] +
        0.15 * df_results['norm_drawdown'] +
        0.10 * df_results['norm_expense']
    )
    
    df_results = df_results.sort_values(by='composite_score', ascending=False)
    
    # Write Scorecard Summary Report
    top_10 = df_results.head(10)
    worst_10 = df_results.tail(10)
    
    scorecard_md = "# Fund Scorecard & Performance Analytics Summary\n\n"
    scorecard_md += f"Calculated over NAV history (Jan 2022 to May 2026) using risk-free rate of {RF_ANNUAL*100:.1f}%. Rankings are based on a composite score weighting Sharpe (30%), Alpha (25%), CAGR (20%), Max Drawdown (15%), and Expense Ratio (10%).\n\n"
    
    scorecard_md += "## TOP 10 MUTUAL FUNDS\n\n"
    scorecard_md += "| Rank | AMFI Code | Scheme Name | Category | CAGR (%) | Sharpe | Alpha (%) | Max Drawdown (%) | Score |\n"
    scorecard_md += "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
    for r, (_, row) in enumerate(top_10.iterrows(), 1):
        scorecard_md += f"| {r} | {row['amfi_code']} | {row['scheme_name']} | {row['category']} | {row['cagr']*100:.2f}% | {row['sharpe_ratio']:.3f} | {row['alpha']*100:.2f}% | {row['max_drawdown_pct']:.2f}% | {row['composite_score']:.1f} |\n"
        
    scorecard_md += "\n## WORST 10 MUTUAL FUNDS\n\n"
    scorecard_md += "| Rank | AMFI Code | Scheme Name | Category | CAGR (%) | Sharpe | Alpha (%) | Max Drawdown (%) | Score |\n"
    scorecard_md += "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
    for r, (_, row) in enumerate(worst_10.iterrows(), 1):
        # Worst 10 starts at Rank 31
        rank_num = 30 + r
        scorecard_md += f"| {rank_num} | {row['amfi_code']} | {row['scheme_name']} | {row['category']} | {row['cagr']*100:.2f}% | {row['sharpe_ratio']:.3f} | {row['alpha']*100:.2f}% | {row['max_drawdown_pct']:.2f}% | {row['composite_score']:.1f} |\n"
        
    with open("reports/fund_scorecard.md", "w", encoding="utf-8") as f:
        f.write(scorecard_md)
    print("Saved reports/fund_scorecard.md.")
    
    # 9. Update fact_performance in SQLite
    print("Updating database table 'fact_performance' with calculated metrics...")
    
    cursor = conn.cursor()
    # Let's inspect the columns of fact_performance in case they mismatch
    cursor.execute("PRAGMA table_info(fact_performance);")
    db_cols = [col[1] for col in cursor.fetchall()]
    
    # Update matching rows in fact_performance
    for _, row in df_results.iterrows():
        # Map values to the fact_performance schema
        # In fact_performance: return_1yr_pct, return_3yr_pct, return_5yr_pct are raw values from CSV,
        # but we can overwrite/set return_3yr_pct to our CAGR, or write new analytical columns if we want.
        # Let's update alpha, beta, sharpe_ratio, sortino_ratio, std_dev_ann_pct, max_drawdown_pct
        cursor.execute("""
            UPDATE fact_performance
            SET alpha = ?,
                beta = ?,
                sharpe_ratio = ?,
                sortino_ratio = ?,
                std_dev_ann_pct = ?,
                max_drawdown_pct = ?,
                is_negative_sharpe = ?
            WHERE amfi_code = ?;
        """, (
            row['alpha'] * 100, # Alpha as percent
            row['beta'],
            row['sharpe_ratio'],
            row['sortino_ratio'],
            row['std_dev_ann_pct'],
            row['max_drawdown_pct'],
            1 if row['sharpe_ratio'] < 0 else 0,
            row['amfi_code']
        ))
        
    conn.commit()
    conn.close()
    print("Database table 'fact_performance' updated successfully.")

if __name__ == "__main__":
    run_performance_analytics()
