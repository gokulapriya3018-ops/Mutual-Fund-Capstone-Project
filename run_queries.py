import sqlite3
import pandas as pd
import os

queries = [
    (
        "Query 1: Top 5 funds by AUM",
        """SELECT amfi_code, scheme_name, fund_house, aum_crore
FROM fact_performance
ORDER BY aum_crore DESC
LIMIT 5;"""
    ),
    (
        "Query 2: Average NAV per month (First 20 rows of results)",
        """SELECT 
    amfi_code,
    strftime('%Y-%m', nav_date) AS month,
    ROUND(AVG(nav), 4) AS avg_nav
FROM fact_nav
GROUP BY amfi_code, month
ORDER BY amfi_code, month
LIMIT 20;"""
    ),
    (
        "Query 3: SIP inflow YoY growth",
        """SELECT
    t1.month,
    t1.sip_inflow_crore,
    t2.sip_inflow_crore AS prev_year_inflow,
    ROUND(((t1.sip_inflow_crore - t2.sip_inflow_crore) / t2.sip_inflow_crore) * 100, 2) AS calculated_yoy_growth_pct,
    t1.yoy_growth_pct AS recorded_yoy_growth_pct
FROM fact_sip_inflows t1
LEFT JOIN fact_sip_inflows t2
    ON substr(t1.month, 6, 2) = substr(t2.month, 6, 2)
    AND CAST(substr(t1.month, 1, 4) AS INTEGER) = CAST(substr(t2.month, 1, 4) AS INTEGER) + 1
ORDER BY t1.month;"""
    ),
    (
        "Query 4: Transactions by state",
        """SELECT state,
       COUNT(*) AS transaction_count,
       ROUND(SUM(amount_inr), 2) AS total_amount_inr
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_inr DESC;"""
    ),
    (
        "Query 5: Funds with expense_ratio < 1%",
        """SELECT amfi_code, scheme_name, fund_house, expense_ratio_pct
FROM dim_fund
WHERE expense_ratio_pct < 1.0
ORDER BY expense_ratio_pct ASC;"""
    ),
    (
        "Query 6: Top 5 sectors by total allocation",
        """SELECT sector,
       ROUND(AVG(weight_pct), 2) AS avg_weight_pct,
       ROUND(SUM(market_value_cr), 2) AS total_market_value_cr
FROM fact_portfolio_holdings
GROUP BY sector
ORDER BY total_market_value_cr DESC
LIMIT 5;"""
    ),
    (
        "Query 7: Demographic analysis of transactions (by age group & gender)",
        """SELECT age_group,
       gender,
       COUNT(*) AS transaction_count,
       ROUND(SUM(amount_inr), 2) AS total_amount_inr,
       ROUND(AVG(amount_inr), 2) AS avg_amount_inr
FROM fact_transactions
GROUP BY age_group, gender
ORDER BY age_group, gender;"""
    ),
    (
        "Query 8: Benchmark performance comparison (average returns by benchmark)",
        """SELECT benchmark,
       COUNT(*) AS fund_count,
       ROUND(AVG(return_1yr_pct), 2) AS avg_return_1yr_pct,
       ROUND(AVG(return_3yr_pct), 2) AS avg_return_3yr_pct,
       ROUND(AVG(return_5yr_pct), 2) AS avg_return_5yr_pct
FROM dim_fund f
JOIN fact_performance p ON f.amfi_code = p.amfi_code
GROUP BY benchmark
ORDER BY avg_return_3yr_pct DESC;"""
    ),
    (
        "Query 9: Top performing fund (3yr return) by risk category",
        """WITH ranked_funds AS (
    SELECT f.risk_category,
           f.amfi_code,
           f.scheme_name,
           p.return_3yr_pct,
           ROW_NUMBER() OVER (PARTITION BY f.risk_category ORDER BY p.return_3yr_pct DESC) as rn
    FROM dim_fund f
    JOIN fact_performance p ON f.amfi_code = p.amfi_code
)
SELECT risk_category, amfi_code, scheme_name, return_3yr_pct
FROM ranked_funds
WHERE rn = 1
ORDER BY return_3yr_pct DESC;"""
    ),
    (
        "Query 10: Transaction volume/value by payment mode and city tier",
        """SELECT city_tier,
       payment_mode,
       COUNT(*) AS transaction_count,
       ROUND(SUM(amount_inr), 2) AS total_amount_inr
FROM fact_transactions
GROUP BY city_tier, payment_mode
ORDER BY city_tier, total_amount_inr DESC;"""
    )
]

def to_markdown_table(df):
    cols = df.columns.tolist()
    header = "| " + " | ".join(map(str, cols)) + " |"
    separator = "| " + " | ".join(["---"] * len(cols)) + " |"
    rows = []
    for _, row in df.iterrows():
        rows.append("| " + " | ".join(map(lambda x: str(x).replace("\n", " ").strip() if x is not None else "", row.tolist())) + " |")
    return "\n".join([header, separator] + rows)

def run_all_queries():
    db_file = "bluestock_mf.db"
    if not os.path.exists(db_file):
        print(f"Error: Database {db_file} does not exist.")
        return
        
    conn = sqlite3.connect(db_file)
    output_file = os.path.join("sql", "queries.sql")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("-- Mutual Fund Analytics SQL Queries and Results\n")
        f.write(f"-- Executed against {db_file}\n\n")
        
        for name, sql in queries:
            print(f"Executing: {name}...")
            df = pd.read_sql_query(sql, conn)
            
            f.write(f"/* =============================================================================\n")
            f.write(f"   {name}\n")
            f.write(f"   ============================================================================= */\n\n")
            f.write(sql)
            f.write(";\n\n")
            
            f.write("/* Result:\n")
            f.write(to_markdown_table(df))
            f.write("\n*/\n\n\n")
            
    conn.close()
    print(f"All queries executed successfully and results saved to {output_file}")

if __name__ == "__main__":
    run_all_queries()
