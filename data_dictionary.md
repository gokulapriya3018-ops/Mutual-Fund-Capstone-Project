# Mutual Fund Analytics Data Dictionary

This document describes the schema, data types, sources, and column descriptions of the tables loaded into the `bluestock_mf.db` SQLite database.

---

## 1. dim_fund (Fund Master)
* **Source Raw Dataset:** `01_fund_master.csv`
* **Type:** Dimension Table
* **Description:** Contains master data for all 40 mutual fund schemes tracked in this project.

| Column Name | SQL Type | Description |
| :--- | :--- | :--- |
| `amfi_code` | TEXT (PK) | Association of Mutual Funds in India code for the scheme. Unique identifier. |
| `fund_house` | TEXT | Name of the Asset Management Company (AMC). |
| `scheme_name` | TEXT | Complete name of the mutual fund scheme. |
| `category` | TEXT | Asset category (e.g., Equity, Debt, Hybrid). |
| `sub_category` | TEXT | Specific strategy or cap size (e.g., Large Cap, Mid Cap, Gilt, Liquid). |
| `plan` | TEXT | Growth plan type (Regular or Direct). |
| `launch_date` | DATE | Date the fund was launched (formatted as `YYYY-MM-DD`). |
| `benchmark` | TEXT | Index against which fund performance is compared. |
| `expense_ratio_pct` | REAL | Yearly fee charged to manage the fund, as a percentage of AUM. |
| `exit_load_pct` | REAL | Fee charged when units are redeemed within a specific period. |
| `min_sip_amount` | REAL | Minimum amount required for a Systematic Investment Plan contribution. |
| `min_lumpsum_amount` | REAL | Minimum amount required for one-time lumpsum investment. |
| `fund_manager` | TEXT | Name of the primary professional managing the fund. |
| `risk_category` | TEXT | Risk classification (Low, Moderate, High, Very High, etc.). |
| `sebi_category_code` | TEXT | Code corresponding to SEBI classification standards. |

---

## 2. fact_nav (Daily NAV History)
* **Source Raw Dataset:** `02_nav_history.csv`
* **Type:** Fact Table
* **Description:** Daily Net Asset Value (NAV) historical records for each scheme. Missing weekday NAVs (market holidays) are forward-filled.

| Column Name | SQL Type | Description |
| :--- | :--- | :--- |
| `amfi_code` | TEXT (FK) | References `dim_fund.amfi_code`. |
| `nav_date` | DATE | Business day date (formatted as `YYYY-MM-DD`). |
| `nav` | REAL | Net Asset Value (per unit price) on the date. |
| `daily_return` | REAL | Computed percent change in NAV from the previous business day: $(NAV_t - NAV_{t-1}) / NAV_{t-1}$. |

---

## 3. fact_transactions (Investor Transactions)
* **Source Raw Dataset:** `08_investor_transactions.csv`
* **Type:** Fact Table
* **Description:** Granular records of individual investor transactions, including investor profile details.

| Column Name | SQL Type | Description |
| :--- | :--- | :--- |
| `transaction_id` | INTEGER (PK) | Auto-incrementing unique identifier for each transaction. |
| `investor_id` | TEXT | Unique code identifying the investor. |
| `transaction_date` | DATE | Date of transaction execution (formatted as `YYYY-MM-DD`). |
| `amfi_code` | TEXT (FK) | References `dim_fund.amfi_code`. |
| `transaction_type` | TEXT | Type of transaction (`SIP`, `Lumpsum`, or `Redemption`). |
| `amount_inr` | REAL | Amount invested or redeemed in Indian Rupees (must be > 0). |
| `state` | TEXT | Investor's state of residence. |
| `city` | TEXT | Investor's city of residence. |
| `city_tier` | TEXT | Classification of city size/activity (T30 = Top 30 cities, B30 = Beyond Top 30). |
| `age_group` | TEXT | Age range of the investor (e.g., 18-25, 26-35, 36-45, 56+). |
| `gender` | TEXT | Gender of the investor. |
| `annual_income_lakh` | REAL | Annual income range of the investor in Lakhs INR. |
| `payment_mode` | TEXT | Mechanism of payment (Net Banking, UPI, Cheque, Mandate). |
| `kyc_status` | TEXT | Know Your Customer compliance status (`Verified` or `Pending`). |

---

## 4. fact_performance (Scheme Performance Metrics)
* **Source Raw Dataset:** `07_scheme_performance.csv`
* **Type:** Fact Table
* **Description:** Summary performance indicators, risk-reward ratios, and ratings for each mutual fund scheme.

| Column Name | SQL Type | Description |
| :--- | :--- | :--- |
| `amfi_code` | TEXT (PK, FK) | References `dim_fund.amfi_code`. |
| `scheme_name` | TEXT | Name of the mutual fund scheme. |
| `fund_house` | TEXT | Asset Management Company (AMC) name. |
| `category` | TEXT | Category of fund. |
| `plan` | TEXT | Regular or Direct plan. |
| `return_1yr_pct` | REAL | 1-year trailing return percentage. |
| `return_3yr_pct` | REAL | 3-year annualized return percentage. |
| `return_5yr_pct` | REAL | 5-year annualized return percentage. |
| `benchmark_3yr_pct` | REAL | 3-year annualized benchmark return percentage. |
| `alpha` | REAL | Excess return of the fund relative to the return of its benchmark index. |
| `beta` | REAL | Measure of the fund's volatility relative to its benchmark index. |
| `sharpe_ratio` | REAL | Risk-adjusted return measure (Average excess return / Standard deviation). |
| `sortino_ratio` | REAL | Measure of risk-adjusted return focusing on downside deviation. |
| `std_dev_ann_pct` | REAL | Annualized standard deviation of returns (measure of volatility). |
| `max_drawdown_pct` | REAL | Maximum peak-to-trough drop in valuation, expressed as a negative percentage. |
| `aum_crore` | REAL | Total Assets Under Management in Crores INR. |
| `expense_ratio_pct` | REAL | Management fees and operating expenses as a percentage. |
| `morningstar_rating`| INTEGER | Performance-based rating out of 5 stars (0 if unrated). |
| `risk_grade` | TEXT | Qualitative risk designation (Moderate, High, Very High, etc.). |
| `is_negative_sharpe`| INTEGER | Binary indicator flag (1 = Sharpe ratio < 0, 0 = Sharpe ratio >= 0). |

---

## 5. fact_portfolio_holdings (Portfolio Holdings Detail)
* **Source Raw Dataset:** `09_portfolio_holdings.csv`
* **Type:** Fact Table
* **Description:** Top constituent stock holdings and sector allocations for each scheme.

| Column Name | SQL Type | Description |
| :--- | :--- | :--- |
| `amfi_code` | TEXT (PK, FK) | References `dim_fund.amfi_code`. |
| `stock_symbol` | TEXT (PK) | Stock exchange ticker symbol for the holding. |
| `stock_name` | TEXT | Company name of the stock holding. |
| `sector` | TEXT | Industrial sector classification of the holding (Banking, IT, Utilities, etc.). |
| `weight_pct` | REAL | Portfolio allocation percentage weight. |
| `market_value_cr` | REAL | Total value of holding in Crores INR. |
| `current_price_inr` | REAL | Market price per share of the holding. |
| `portfolio_date` | DATE | Date of portfolio disclosure reporting. |

---

## 6. fact_benchmark_indices (Benchmark Indices Closing Values)
* **Source Raw Dataset:** `10_benchmark_indices.csv`
* **Type:** Fact Table
* **Description:** Historical daily closing prices of benchmark indexes.

| Column Name | SQL Type | Description |
| :--- | :--- | :--- |
| `date` | DATE (PK) | Business date (formatted as `YYYY-MM-DD`). |
| `index_name` | TEXT (PK) | Name of the benchmark index (e.g. NIFTY50, NIFTY100, etc.). |
| `close_value` | REAL | Closing price value of the index on the date. |

---

## 7. fact_sip_inflows (Monthly SIP Inflows)
* **Source Raw Dataset:** `04_monthly_sip_inflows.csv`
* **Type:** Fact Table
* **Description:** Industry-wide monthly stats of SIP investment volumes and YoY growths.

| Column Name | SQL Type | Description |
| :--- | :--- | :--- |
| `month` | TEXT (PK) | Month identifier formatted as `YYYY-MM`. |
| `sip_inflow_crore` | REAL | Monthly SIP contributions received by the industry in Crores INR. |
| `active_sip_accounts_crore` | REAL | Count of active SIP accounts in Crores. |
| `new_sip_accounts_lakh` | REAL | Count of new SIP accounts registered in the month in Lakhs. |
| `sip_aum_lakh_crore` | REAL | Cumulative AUM accumulated via SIPs in Lakh Crores INR. |
| `yoy_growth_pct` | REAL | Year-over-Year growth percentage of monthly SIP inflows. |

---

## 8. fact_category_inflows (Category Wise Monthly Inflows)
* **Source Raw Dataset:** `05_category_inflows.csv`
* **Type:** Fact Table
* **Description:** Monthly net flows into different mutual fund categories.

| Column Name | SQL Type | Description |
| :--- | :--- | :--- |
| `month` | TEXT (PK) | Month identifier formatted as `YYYY-MM`. |
| `category` | TEXT (PK) | Mutual fund category name (e.g. Mid Cap, Large Cap, ELSS). |
| `net_inflow_crore` | REAL | Net monthly inflows (Inflows - Redemptions) in Crores INR. |

---

## 9. dim_aum_fund_house (AUM By Fund House)
* **Source Raw Dataset:** `03_aum_by_fund_house.csv`
* **Type:** Dimension Table
* **Description:** Periodic AUM valuation and scheme counts categorized by AMC (Fund House).

| Column Name | SQL Type | Description |
| :--- | :--- | :--- |
| `date` | DATE (PK) | Date of AUM statement (formatted as `YYYY-MM-DD`). |
| `fund_house` | TEXT (PK) | Name of the Asset Management Company. |
| `aum_lakh_crore` | REAL | AUM value in Lakh Crores INR. |
| `aum_crore` | REAL | AUM value in Crores INR. |
| `num_schemes` | INTEGER | Number of mutual fund schemes managed by the AMC. |

---

## 10. dim_industry_folio (Industry Folio Counts)
* **Source Raw Dataset:** `06_industry_folio_count.csv`
* **Type:** Dimension Table
* **Description:** Folio counts and summary stats across mutual fund types on a periodic basis.

| Column Name | SQL Type | Description |
| :--- | :--- | :--- |
| `month` | TEXT (PK) | Reporting month (formatted as `YYYY-MM`). |
| `total_folios_crore` | REAL | Total folios in the industry in Crores. |
| `equity_folios_crore` | REAL | Total equity folios in Crores. |
| `debt_folios_crore` | REAL | Total debt folios in Crores. |
| `hybrid_folios_crore` | REAL | Total hybrid folios in Crores. |
| `others_folios_crore` | REAL | Other folio classifications in Crores. |
