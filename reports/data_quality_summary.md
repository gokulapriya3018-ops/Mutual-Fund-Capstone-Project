# Data Quality Summary Report (Day 1 Ingestion)

Generated automatically after inspecting 10 datasets.

## Dataset Health Matrix

| Dataset Name | Rows | Columns | Nulls | Duplicates | Anomalies Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 01_fund_master.csv | 40 | 15 | 0 | 0 | ✅ Healthy |
| 02_nav_history.csv | 46000 | 3 | 0 | 0 | ✅ Healthy |
| 03_aum_by_fund_house.csv | 90 | 5 | 0 | 0 | ✅ Healthy |
| 04_monthly_sip_inflows.csv | 48 | 6 | 12 | 0 | ⚠️ Issue(s) found |
| 05_category_inflows.csv | 144 | 3 | 0 | 0 | ✅ Healthy |
| 06_industry_folio_count.csv | 21 | 6 | 0 | 0 | ✅ Healthy |
| 07_scheme_performance.csv | 40 | 19 | 0 | 0 | ⚠️ Issue(s) found |
| 08_investor_transactions.csv | 32778 | 13 | 0 | 0 | ✅ Healthy |
| 09_portfolio_holdings.csv | 322 | 8 | 0 | 0 | ✅ Healthy |
| 10_benchmark_indices.csv | 8050 | 3 | 0 | 0 | ✅ Healthy |

## Detailed Anomalies By File

### 04_monthly_sip_inflows.csv
- Missing values found: {'yoy_growth_pct': 12}

### 07_scheme_performance.csv
- Negative values (40) found in column 'max_drawdown_pct'


## AMFI Code Validation Results

- Unique AMFI codes in fund_master: **40**
- Unique AMFI codes in nav_history: **40**
- **PASS**: Every AMFI code in fund_master exists in nav_history.
- **NOTE**: No extra AMFI codes exist in nav_history.
