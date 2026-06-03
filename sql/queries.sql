-- Mutual Fund Analytics SQL Queries and Results
-- Executed against bluestock_mf.db

/* =============================================================================
   Query 1: Top 5 funds by AUM
   ============================================================================= */

SELECT amfi_code, scheme_name, fund_house, aum_crore
FROM fact_performance
ORDER BY aum_crore DESC
LIMIT 5;;

/* Result:
| amfi_code | scheme_name | fund_house | aum_crore |
| --- | --- | --- | --- |
| 148568 | Mirae Asset Emerging Bluechip Fund - Regular - Growth | Mirae Asset MF | 49046.0 |
| 120842 | Kotak Emerging Equity Fund - Regular - Growth | Kotak Mahindra MF | 47469.0 |
| 118634 | Nippon India Small Cap Fund - Regular - Growth | Nippon India MF | 43630.0 |
| 149322 | DSP Top 100 Equity Fund - Regular - Growth | DSP Mutual Fund | 41828.0 |
| 102886 | UTI Mid Cap Fund - Regular - Growth | UTI Mutual Fund | 41728.0 |
*/


/* =============================================================================
   Query 2: Average NAV per month (First 20 rows of results)
   ============================================================================= */

SELECT 
    amfi_code,
    strftime('%Y-%m', nav_date) AS month,
    ROUND(AVG(nav), 4) AS avg_nav
FROM fact_nav
GROUP BY amfi_code, month
ORDER BY amfi_code, month
LIMIT 20;;

/* Result:
| amfi_code | month | avg_nav |
| --- | --- | --- |
| 100016 | 2022-01 | 512.5353 |
| 100016 | 2022-02 | 513.9306 |
| 100016 | 2022-03 | 522.5782 |
| 100016 | 2022-04 | 525.6312 |
| 100016 | 2022-05 | 504.3125 |
| 100016 | 2022-06 | 465.137 |
| 100016 | 2022-07 | 436.746 |
| 100016 | 2022-08 | 421.3311 |
| 100016 | 2022-09 | 422.1759 |
| 100016 | 2022-10 | 431.4175 |
| 100016 | 2022-11 | 463.6936 |
| 100016 | 2022-12 | 480.9635 |
| 100016 | 2023-01 | 490.9673 |
| 100016 | 2023-02 | 493.1681 |
| 100016 | 2023-03 | 546.0677 |
| 100016 | 2023-04 | 566.9077 |
| 100016 | 2023-05 | 566.0106 |
| 100016 | 2023-06 | 571.042 |
| 100016 | 2023-07 | 578.758 |
| 100016 | 2023-08 | 569.4809 |
*/


/* =============================================================================
   Query 3: SIP inflow YoY growth
   ============================================================================= */

SELECT
    t1.month,
    t1.sip_inflow_crore,
    t2.sip_inflow_crore AS prev_year_inflow,
    ROUND(((t1.sip_inflow_crore - t2.sip_inflow_crore) / t2.sip_inflow_crore) * 100, 2) AS calculated_yoy_growth_pct,
    t1.yoy_growth_pct AS recorded_yoy_growth_pct
FROM fact_sip_inflows t1
LEFT JOIN fact_sip_inflows t2
    ON substr(t1.month, 6, 2) = substr(t2.month, 6, 2)
    AND CAST(substr(t1.month, 1, 4) AS INTEGER) = CAST(substr(t2.month, 1, 4) AS INTEGER) + 1
ORDER BY t1.month;;

/* Result:
| month | sip_inflow_crore | prev_year_inflow | calculated_yoy_growth_pct | recorded_yoy_growth_pct |
| --- | --- | --- | --- | --- |
| 2022-01 | 11517.0 | nan | nan | nan |
| 2022-02 | 11438.0 | nan | nan | nan |
| 2022-03 | 12328.0 | nan | nan | nan |
| 2022-04 | 11863.0 | nan | nan | nan |
| 2022-05 | 12286.0 | nan | nan | nan |
| 2022-06 | 12276.0 | nan | nan | nan |
| 2022-07 | 12140.0 | nan | nan | nan |
| 2022-08 | 12694.0 | nan | nan | nan |
| 2022-09 | 12976.0 | nan | nan | nan |
| 2022-10 | 13040.0 | nan | nan | nan |
| 2022-11 | 13306.0 | nan | nan | nan |
| 2022-12 | 13573.0 | nan | nan | nan |
| 2023-01 | 13856.0 | 11517.0 | 20.31 | 20.31 |
| 2023-02 | 13687.0 | 11438.0 | 19.66 | 19.66 |
| 2023-03 | 14276.0 | 12328.0 | 15.8 | 15.8 |
| 2023-04 | 14749.0 | 11863.0 | 24.33 | 24.33 |
| 2023-05 | 14749.0 | 12286.0 | 20.05 | 20.05 |
| 2023-06 | 14734.0 | 12276.0 | 20.02 | 20.02 |
| 2023-07 | 15245.0 | 12140.0 | 25.58 | 25.58 |
| 2023-08 | 15814.0 | 12694.0 | 24.58 | 24.58 |
| 2023-09 | 16042.0 | 12976.0 | 23.63 | 23.63 |
| 2023-10 | 16928.0 | 13040.0 | 29.82 | 29.82 |
| 2023-11 | 17073.0 | 13306.0 | 28.31 | 28.31 |
| 2023-12 | 17610.0 | 13573.0 | 29.74 | 29.74 |
| 2024-01 | 18838.0 | 13856.0 | 35.96 | 35.96 |
| 2024-02 | 19187.0 | 13687.0 | 40.18 | 40.18 |
| 2024-03 | 20371.0 | 14276.0 | 42.69 | 42.69 |
| 2024-04 | 20371.0 | 14749.0 | 38.12 | 38.12 |
| 2024-05 | 21262.0 | 14749.0 | 44.16 | 44.16 |
| 2024-06 | 21262.0 | 14734.0 | 44.31 | 44.31 |
| 2024-07 | 23332.0 | 15245.0 | 53.05 | 53.05 |
| 2024-08 | 23547.0 | 15814.0 | 48.9 | 48.9 |
| 2024-09 | 24509.0 | 16042.0 | 52.78 | 52.78 |
| 2024-10 | 25323.0 | 16928.0 | 49.59 | 49.59 |
| 2024-11 | 25320.0 | 17073.0 | 48.3 | 48.3 |
| 2024-12 | 26459.0 | 17610.0 | 50.25 | 50.25 |
| 2025-01 | 26400.0 | 18838.0 | 40.14 | 40.14 |
| 2025-02 | 25999.0 | 19187.0 | 35.5 | 35.5 |
| 2025-03 | 25926.0 | 20371.0 | 27.27 | 27.27 |
| 2025-04 | 26632.0 | 20371.0 | 30.73 | 30.73 |
| 2025-05 | 26688.0 | 21262.0 | 25.52 | 25.52 |
| 2025-06 | 27274.0 | 21262.0 | 28.28 | 28.28 |
| 2025-07 | 28464.0 | 23332.0 | 22.0 | 22.0 |
| 2025-08 | 28265.0 | 23547.0 | 20.04 | 20.04 |
| 2025-09 | 29361.0 | 24509.0 | 19.8 | 19.8 |
| 2025-10 | 29529.0 | 25323.0 | 16.61 | 16.61 |
| 2025-11 | 30200.0 | 25320.0 | 19.27 | 19.27 |
| 2025-12 | 31002.0 | 26459.0 | 17.17 | 17.17 |
*/


/* =============================================================================
   Query 4: Transactions by state
   ============================================================================= */

SELECT state,
       COUNT(*) AS transaction_count,
       ROUND(SUM(amount_inr), 2) AS total_amount_inr
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_inr DESC;;

/* Result:
| state | transaction_count | total_amount_inr |
| --- | --- | --- |
| Punjab | 2965 | 315780459.0 |
| Tamil Nadu | 2806 | 315177237.0 |
| Madhya Pradesh | 2931 | 308312493.0 |
| Rajasthan | 2577 | 298645822.0 |
| Gujarat | 2780 | 298358940.0 |
| West Bengal | 2748 | 297182514.0 |
| Telangana | 2718 | 290219284.0 |
| Delhi | 2677 | 289633404.0 |
| Uttar Pradesh | 2695 | 285368873.0 |
| Haryana | 2736 | 279634354.0 |
| Karnataka | 2621 | 273753570.0 |
| Maharashtra | 2524 | 269513480.0 |
*/


/* =============================================================================
   Query 5: Funds with expense_ratio < 1%
   ============================================================================= */

SELECT amfi_code, scheme_name, fund_house, expense_ratio_pct
FROM dim_fund
WHERE expense_ratio_pct < 1.0
ORDER BY expense_ratio_pct ASC;;

/* Result:
| amfi_code | scheme_name | fund_house | expense_ratio_pct |
| --- | --- | --- | --- |
| 118636 | Nippon India Gilt Securities Fund - Regular - Growth | Nippon India MF | 0.55 |
| 100025 | HDFC Short Term Debt Fund - Regular - Growth | HDFC Mutual Fund | 0.56 |
| 120844 | Kotak Liquid Fund - Regular - Growth | Kotak Mahindra MF | 0.6 |
| 119552 | SBI Bluechip Fund - Direct Plan - Growth | SBI Mutual Fund | 0.66 |
| 119599 | SBI Small Cap Fund - Direct Plan - Growth | SBI Mutual Fund | 0.72 |
| 118633 | Nippon India Large Cap Fund - Direct - Growth | Nippon India MF | 0.72 |
| 120507 | ICICI Pru Liquid Fund - Regular - Growth | ICICI Prudential MF | 0.74 |
| 119093 | Axis Bluechip Fund - Direct - Growth | Axis Mutual Fund | 0.75 |
| 119120 | SBI Magnum Gilt Fund - Regular Plan - Growth | SBI Mutual Fund | 0.77 |
| 125498 | HDFC Mid-Cap Opportunities Fund - Direct - Growth | HDFC Mutual Fund | 0.78 |
| 101208 | ABSL Liquid Fund - Regular - Growth | Aditya Birla Sun Life MF | 0.79 |
| 120504 | ICICI Pru Bluechip Fund - Direct - Growth | ICICI Prudential MF | 0.8 |
| 118635 | Nippon India ETF Nifty 50 BeES | Nippon India MF | 0.89 |
| 125497 | HDFC Top 100 Fund - Direct Plan - Growth | HDFC Mutual Fund | 0.92 |
*/


/* =============================================================================
   Query 6: Top 5 sectors by total allocation
   ============================================================================= */

SELECT sector,
       ROUND(AVG(weight_pct), 2) AS avg_weight_pct,
       ROUND(SUM(market_value_cr), 2) AS total_market_value_cr
FROM fact_portfolio_holdings
GROUP BY sector
ORDER BY total_market_value_cr DESC
LIMIT 5;;

/* Result:
| sector | avg_weight_pct | total_market_value_cr |
| --- | --- | --- |
| Banking | 10.87 | 62840.29 |
| IT | 11.39 | 38477.11 |
| Pharma | 10.72 | 34606.1 |
| Automobile | 9.81 | 34296.97 |
| Utilities | 11.06 | 25108.63 |
*/


/* =============================================================================
   Query 7: Demographic analysis of transactions (by age group & gender)
   ============================================================================= */

SELECT age_group,
       gender,
       COUNT(*) AS transaction_count,
       ROUND(SUM(amount_inr), 2) AS total_amount_inr,
       ROUND(AVG(amount_inr), 2) AS avg_amount_inr
FROM fact_transactions
GROUP BY age_group, gender
ORDER BY age_group, gender;;

/* Result:
| age_group | gender | transaction_count | total_amount_inr | avg_amount_inr |
| --- | --- | --- | --- | --- |
| 18-25 | Female | 1722 | 186666955.0 | 108401.25 |
| 18-25 | Male | 3194 | 344972437.0 | 108006.4 |
| 26-35 | Female | 4379 | 465160464.0 | 106225.27 |
| 26-35 | Male | 9084 | 986439754.0 | 108590.9 |
| 36-45 | Female | 2705 | 293392039.0 | 108462.86 |
| 36-45 | Male | 5441 | 578255489.0 | 106277.43 |
| 46-55 | Female | 1270 | 140314877.0 | 110484.16 |
| 46-55 | Male | 2509 | 265091592.0 | 105656.27 |
| 56+ | Female | 893 | 90812366.0 | 101693.58 |
| 56+ | Male | 1581 | 170474457.0 | 107826.98 |
*/


/* =============================================================================
   Query 8: Benchmark performance comparison (average returns by benchmark)
   ============================================================================= */

SELECT benchmark,
       COUNT(*) AS fund_count,
       ROUND(AVG(return_1yr_pct), 2) AS avg_return_1yr_pct,
       ROUND(AVG(return_3yr_pct), 2) AS avg_return_3yr_pct,
       ROUND(AVG(return_5yr_pct), 2) AS avg_return_5yr_pct
FROM dim_fund f
JOIN fact_performance p ON f.amfi_code = p.amfi_code
GROUP BY benchmark
ORDER BY avg_return_3yr_pct DESC;;

/* Result:
| benchmark | fund_count | avg_return_1yr_pct | avg_return_3yr_pct | avg_return_5yr_pct |
| --- | --- | --- | --- | --- |
| BSE 250 SmallCap TRI | 6 | 22.26 | 21.69 | 21.9 |
| NIFTY Midcap 150 TRI | 6 | 16.16 | 16.82 | 17.28 |
| NIFTY Midcap 50 TRI | 1 | 14.88 | 15.18 | 18.94 |
| NIFTY 500 TRI | 4 | 15.25 | 14.83 | 14.04 |
| NIFTY Large Midcap 250 TRI | 1 | 14.91 | 14.56 | 15.68 |
| NIFTY 100 TRI | 14 | 13.72 | 12.99 | 13.32 |
| NIFTY 50 TRI | 2 | 11.95 | 11.93 | 11.81 |
| CRISIL Short Term Bond Index | 1 | 6.83 | 7.37 | 6.41 |
| CRISIL Liquid Fund AI Index | 3 | 6.44 | 6.33 | 8.05 |
| CRISIL Dynamic Gilt Index | 2 | 5.77 | 5.69 | 7.07 |
*/


/* =============================================================================
   Query 9: Top performing fund (3yr return) by risk category
   ============================================================================= */

WITH ranked_funds AS (
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
ORDER BY return_3yr_pct DESC;;

/* Result:
| risk_category | amfi_code | scheme_name | return_3yr_pct |
| --- | --- | --- | --- |
| Very High | 119598 | SBI Small Cap Fund - Regular Plan - Growth | 23.39 |
| High | 120842 | Kotak Emerging Equity Fund - Regular - Growth | 18.23 |
| Moderately High | 120843 | Kotak Flexicap Fund - Regular - Growth | 15.65 |
| Moderate | 100016 | HDFC Top 100 Fund - Regular Plan - Growth | 14.84 |
| Low | 120507 | ICICI Pru Liquid Fund - Regular - Growth | 7.68 |
*/


/* =============================================================================
   Query 10: Transaction volume/value by payment mode and city tier
   ============================================================================= */

SELECT city_tier,
       payment_mode,
       COUNT(*) AS transaction_count,
       ROUND(SUM(amount_inr), 2) AS total_amount_inr
FROM fact_transactions
GROUP BY city_tier, payment_mode
ORDER BY city_tier, total_amount_inr DESC;;

/* Result:
| city_tier | payment_mode | transaction_count | total_amount_inr |
| --- | --- | --- | --- |
| B30 | Net Banking | 2802 | 309259652.0 |
| B30 | Cheque | 2809 | 303575635.0 |
| B30 | UPI | 2684 | 299343777.0 |
| B30 | Mandate | 2764 | 290146576.0 |
| T30 | UPI | 5470 | 588897244.0 |
| T30 | Cheque | 5419 | 588643583.0 |
| T30 | Net Banking | 5448 | 584232971.0 |
| T30 | Mandate | 5382 | 557480992.0 |
*/


