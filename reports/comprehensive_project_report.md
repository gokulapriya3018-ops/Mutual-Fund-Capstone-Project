# Comprehensive Capstone Project Report
## End-to-End Mutual Fund Analytics Pipeline & Presentation Layer

---

## 1. Executive Summary

This report provides a comprehensive summary of the **Mutual Fund Analytics Capstone Project**, a production-grade data engineering and quantitative analytics system designed for the Indian Mutual Fund industry. 

### Core Accomplishments
1. **Automated ETL Pipeline**: Built an end-to-end pipeline (`data_ingestion.py`, `live_nav_fetch.py`, `clean_and_load.py`) that ingests raw transaction, master, and index datasets, cleans data quality anomalies, handles weekday reindexing with forward-filling for holidays, and loads them into a normalized database.
2. **Relational Database Model**: Designed and populated a star schema in a SQLite database (`bluestock_mf.db`) containing 10 inter-linked dimension and fact tables, holding **over 90,000 records** of historical data.
3. **Quantitative Analytics Engine**: Programmed financial calculations for Trailing Returns, Compounded Annual Growth Rate (CAGR), Sharpe Ratio, Sortino Ratio, CAPM Alpha, Beta, and Maximum Drawdown (MDD) across 40 schemes over a 4.5-year history.
4. **Advanced Risk & Cohort Modeling**: Formulated and calculated daily Value at Risk (VaR), Conditional VaR (CVaR), 90-day rolling Sharpe ratios, Herfindahl-Hirschman Index (HHI) for sector concentrations, and customer cohort retention tracking.
5. **Interactive Web Dashboard**: Developed a 6-page interactive web interface served via a Python backend server (`dashboard/server.py`) offering filters, charts (via Chart.js), scorecards, drill-through analytics, and a recommendation engine.

---

## 2. System Architecture

The pipeline follows a modern decoupled data engineering architecture:

<table style="width: 100%; border: none; border-collapse: collapse; margin-top: 10px; margin-bottom: 10px;">
  <tr>
    <td style="width: 45%; border: 1px solid #2b6cb0; background-color: #f7fafc; padding: 10px; text-align: center; vertical-align: middle;">
      <strong style="color: #1a365d; font-size: 11pt;">1. Raw Ingestion Layer</strong><br/>
      <span style="font-size: 9pt; color: #4a5568;">
        • 10 Raw CSV Datasets<br/>
        • AMFI API (api.mfapi.in) for Live NAV
      </span>
    </td>
    <td style="width: 10%; text-align: center; font-size: 18pt; border: none; vertical-align: middle; color: #2b6cb0;">➔</td>
    <td style="width: 45%; border: 1px solid #2b6cb0; background-color: #f7fafc; padding: 10px; text-align: center; vertical-align: middle;">
      <strong style="color: #1a365d; font-size: 11pt;">2. Data Processing &amp; Storage (ETL)</strong><br/>
      <span style="font-size: 9pt; color: #4a5568;">
        • clean_and_load.py (Standardization)<br/>
        • SQLite Database (bluestock_mf.db)
      </span>
    </td>
  </tr>
  <tr>
    <td colspan="3" style="text-align: center; font-size: 18pt; border: none; padding: 5px; color: #2b6cb0; line-height: 1;">▼</td>
  </tr>
  <tr>
    <td style="width: 45%; border: 1px solid #2b6cb0; background-color: #f7fafc; padding: 10px; text-align: center; vertical-align: middle;">
      <strong style="color: #1a365d; font-size: 11pt;">4. Presentation Layer (Dashboard)</strong><br/>
      <span style="font-size: 9pt; color: #4a5568;">
        • Python Server (dashboard/server.py API)<br/>
        • HTML5/CSS3/JS Web Interface (Chart.js)
      </span>
    </td>
    <td style="width: 10%; text-align: center; font-size: 18pt; border: none; vertical-align: middle; color: #2b6cb0;">◀</td>
    <td style="width: 45%; border: 1px solid #2b6cb0; background-color: #f7fafc; padding: 10px; text-align: center; vertical-align: middle;">
      <strong style="color: #1a365d; font-size: 11pt;">3. Quantitative &amp; Risk Engine</strong><br/>
      <span style="font-size: 9pt; color: #4a5568;">
        • CAGR, Sharpe, Sortino, CAPM Alpha/Beta<br/>
        • VaR, CVaR, HHI, Cohorts, SIP Continuation
      </span>
    </td>
  </tr>
</table>


### Components
* **Data Sources**: Historical daily NAVs, investor transactions (32,778 rows), AMC AUM statements, category inflows, industry folios, benchmark index values (8,050 rows).
* **Storage Layer**: Relational SQLite3 database optimizing storage footprint and enabling complex multi-table joins.
* **Backend Layer**: Multi-threaded Python server serving dynamic REST API endpoints for key metrics, recommendations, cohorts, and fund-specific details.
* **Frontend Layer**: Responsive web interface written in vanilla HTML5, CSS3, and ES6 Javascript, relying on Chart.js for visualization and Font Awesome for icons.

---

## 3. Database Schema Design (Star Schema)

The analytical database `bluestock_mf.db` implements an optimized Star Schema with strict types, constraints, and index-ready primary and foreign keys:

<table style="width: 100%; border: none; border-collapse: collapse; margin-top: 10px; margin-bottom: 10px;">
  <tr>
    <td colspan="3" style="border: 1px solid #4a5568; background-color: #edf2f7; padding: 8px; text-align: center;">
      <strong style="color: #2d3748; font-size: 11pt;">dim_fund (Fund Master Table - Primary Dimension)</strong><br/>
      <span style="font-size: 8.5pt; color: #4a5568;">
        <strong>amfi_code (PK)</strong> | scheme_name | fund_house | category | sub_category | plan | launch_date | benchmark | expense_ratio_pct | min_sip_amount
      </span>
    </td>
  </tr>
  <tr>
    <td colspan="3" style="text-align: center; font-size: 14pt; border: none; color: #4a5568; padding: 3px; line-height: 1;">▼ 1-to-Many Relationships</td>
  </tr>
  <tr>
    <td style="width: 32%; border: 1px solid #2b6cb0; background-color: #ebf8ff; padding: 8px; text-align: center; vertical-align: top;">
      <strong style="color: #2b6cb0; font-size: 9.5pt;">fact_nav</strong><br/>
      <span style="font-size: 8pt; color: #2d3748; line-height: 1.4;">
        <strong>amfi_code (FK, PK)</strong><br/>
        <strong>nav_date (PK)</strong><br/>
        nav<br/>
        daily_return
      </span>
    </td>
    <td style="width: 36%; border: 1px solid #2b6cb0; background-color: #ebf8ff; padding: 8px; text-align: center; vertical-align: top;">
      <strong style="color: #2b6cb0; font-size: 9.5pt;">fact_performance</strong><br/>
      <span style="font-size: 8pt; color: #2d3748; line-height: 1.4;">
        <strong>amfi_code (FK, PK)</strong><br/>
        return_3yr_pct (CAGR)<br/>
        sharpe_ratio | sortino_ratio<br/>
        alpha | beta | max_drawdown_pct<br/>
        aum_crore | expense_ratio_pct
      </span>
    </td>
    <td style="width: 32%; border: 1px solid #2b6cb0; background-color: #ebf8ff; padding: 8px; text-align: center; vertical-align: top;">
      <strong style="color: #2b6cb0; font-size: 9.5pt;">fact_transactions</strong><br/>
      <span style="font-size: 8pt; color: #2d3748; line-height: 1.4;">
        <strong>transaction_id (PK)</strong><br/>
        investor_id | transaction_date<br/>
        <strong>amfi_code (FK)</strong><br/>
        transaction_type | amount_inr<br/>
        state | age_group | payment_mode
      </span>
    </td>
  </tr>
  <tr>
    <td colspan="3" style="height: 10px; border: none;"></td>
  </tr>
  <tr>
    <td style="width: 32%; border: 1px solid #2c5282; background-color: #edf2f7; padding: 8px; text-align: center; vertical-align: top;">
      <strong style="color: #2c5282; font-size: 9.5pt;">fact_portfolio_holdings</strong><br/>
      <span style="font-size: 8pt; color: #2d3748; line-height: 1.4;">
        <strong>amfi_code (FK, PK)</strong><br/>
        <strong>stock_symbol (PK)</strong><br/>
        stock_name | sector<br/>
        weight_pct | market_value_cr
      </span>
    </td>
    <td style="width: 36%; border: 1px solid #2c5282; background-color: #edf2f7; padding: 8px; text-align: center; vertical-align: top;">
      <strong style="color: #2c5282; font-size: 9.5pt;">fact_advanced_risk</strong><br/>
      <span style="font-size: 8pt; color: #2d3748; line-height: 1.4;">
        <strong>amfi_code (FK, PK)</strong><br/>
        var_95_pct<br/>
        cvar_95_pct
      </span>
    </td>
    <td style="width: 32%; border: 1px solid #2c5282; background-color: #edf2f7; padding: 8px; text-align: center; vertical-align: top;">
      <strong style="color: #2c5282; font-size: 9.5pt;">fact_sector_concentration</strong><br/>
      <span style="font-size: 8pt; color: #2d3748; line-height: 1.4;">
        <strong>amfi_code (FK, PK)</strong><br/>
        scheme_name<br/>
        hhi_index<br/>
        concentration_level
      </span>
    </td>
  </tr>
</table>


---

## 4. Data Pipeline & ETL Process

### Data Quality Auditing & Cleaning
During ingestion, multiple data quality anomalies were identified and resolved programmatically in `clean_and_load.py`:
* **Reindexing to Standard Business Days (`freq='B'`)**: The raw `02_nav_history.csv` was missing market holidays. To prevent gaps in calculations, each scheme's NAV series was reindexed to include every Monday-through-Friday business day (1,150 unique dates from Jan 3, 2022 to May 29, 2026). The missing NAV values were forward-filled (`ffill()`).
* **Transaction Standardization**: Cleaned `transaction_type` in `08_investor_transactions.csv` to map strictly to `SIP`, `Lumpsum`, or `Redemption`. Transaction amounts were verified to be strictly positive (> 0).
* **KYC Field Correction**: Sanitized KYC status flags to ensure values map strictly to `Verified` or `Pending`.
* **Out-of-Bounds Ratios**: Audited expense ratios to verify they lie in standard boundaries `[0.1%, 2.5%]`. Corrected drawdown representation (standardized as negative values).

---

## 5. Quantitative Analytics Calculations

The engine performs critical portfolio risk and return evaluations based on the following formulas:

### Trailing NAV Return
<blockquote>
<strong>Daily Return Formula:</strong><br/>
Return<sub>t</sub> = (NAV<sub>t</sub> - NAV<sub>t-1</sub>) / NAV<sub>t-1</sub>
</blockquote>

### Compounded Annual Growth Rate (CAGR)
Annualized growth rate over a fund's historical span:
<blockquote>
<strong>Compounded Annual Growth Rate (CAGR) Formula:</strong><br/>
CAGR = (Ending Value / Beginning Value)<sup>(365.25 / Days)</sup> - 1
</blockquote>

### Sharpe Ratio
Risk-adjusted performance utilizing an annualized risk-free rate (R<sub>f</sub>) of 6.0%:
<blockquote>
<strong>Sharpe Ratio Formula:</strong><br/>
Sharpe Ratio = (R<sub>annualized</sub> - R<sub>f</sub>) / σ<sub>annualized</sub><br/>
<span style="font-size: 8.5pt; color: #4a5568;">Where R<sub>annualized</sub> = Mean(Daily Return) × 252, and σ<sub>annualized</sub> = Standard Deviation(Daily Return) × √252</span>
</blockquote>

### Sortino Ratio
Focuses on downside volatility (R<sub>p,t</sub> < R<sub>f, daily</sub>) rather than total deviation:
<blockquote>
<strong>Sortino Ratio Formula:</strong><br/>
Sortino Ratio = (R<sub>annualized</sub> - R<sub>f</sub>) / σ<sub>downside, annualized</sub><br/>
<span style="font-size: 8.5pt; color: #4a5568;">Where σ<sub>downside, annualized</sub> is the standard deviation of only negative daily returns scaled by √252</span>
</blockquote>

### CAPM Alpha (α) & Beta (β)
* **Beta (β)**: Measure of systemic market volatility matching the fund to its index (e.g. NIFTY 100):
<blockquote>
<strong>CAPM Beta (β) Formula:</strong><br/>
Beta (β) = Covariance(R<sub>fund</sub>, R<sub>market</sub>) / Variance(R<sub>market</sub>)
</blockquote>
* **Alpha (α)**: Outperformance generated by the manager relative to the index adjusted for risk:
<blockquote>
<strong>CAPM Alpha (α) Formula:</strong><br/>
Alpha (α) = R<sub>fund, annualized</sub> - [R<sub>f</sub> + β × (R<sub>market, annualized</sub> - R<sub>f</sub>)]
</blockquote>

### Maximum Drawdown (MDD)
The peak-to-trough drop in NAV representing the worst-case potential loss:
<blockquote>
<strong>Maximum Drawdown (MDD) Formulas:</strong><br/>
Drawdown<sub>t</sub> = (NAV<sub>t</sub> - Peak<sub>t</sub>) / Peak<sub>t</sub><br/>
MDD = Minimum(Drawdown<sub>t</sub>)
</blockquote>

---


## 6. Advanced Risk & Strategy Analytics

Beyond basic ratios, the analytics engine computes advanced risk models:

### 1. Value at Risk (VaR) & Conditional VaR (CVaR)
* **95% Daily VaR**: The 5th percentile of daily return history. It indicates that there is a 95% probability that the daily loss will not exceed this threshold.
* **95% Daily CVaR**: The expected value of daily losses given that they exceed the 95% VaR threshold (capturing tail-risk).

### 2. Herfindahl-Hirschman Index (HHI) for Sector Allocation
Calculates diversification concentration based on sector weights (w<sub>i</sub>):
<blockquote>
<strong>Herfindahl-Hirschman Index (HHI) Formula:</strong><br/>
HHI = Σ (w<sub>i</sub>)<sup>2</sup><br/>
<span style="font-size: 8.5pt; color: #4a5568;">Where w<sub>i</sub> is the weight percentage of sector/stock i.</span>
</blockquote>
* **HHI < 1,500**: Diversified
* **HHI 1,500 – 2,500**: Moderately Concentrated
* **HHI > 2,500**: Highly Concentrated

### 3. Investor Cohort Analysis
Tracks groups of investors based on their onboarding quarter (cohort) to study long-term retention decay:
<blockquote>
<strong>Retention Rate Formula:</strong><br/>
Retention Rate<sub>t</sub> = Active Investors in Quarter t / Cohort Size
</blockquote>


### 4. SIP Continuation & Retention Alerts
Classifies Systematic Investment Plan (SIP) investors by transaction recency:
* **Active**: Transaction observed within the last 35 days.
* **At Risk**: No transaction observed in the last 35 days (triggering retention efforts).

---

## 7. Business & Analytical Insights

Running analytical queries on the relational database yields structural insights:

### A. Database Overview Metrics
* **Total Assets Under Management (AUM)**: **1,043,664.00 Crore INR** (~10.4 Lakh Crore INR)
* **Total Scheme Count**: **40 Mutual Funds**
* **Total Transactions Audited**: **32,778**
* **Active Investors**: **5,000 Unique Customers**
* **Cumulative Transaction Value**: **3,521,580,430.00 INR** (~352 Crore INR)

### B. Mutual Fund Performance Scorecard (CAGR & Sharpe)
Funds are ranked based on a weighted scorecard (Sharpe: 30%, Alpha: 25%, CAGR: 20%, MDD: 15%, Expense Ratio: 10%):

> [!NOTE]
> Mid-cap and Large-cap Equity funds dominated the top rankings due to substantial growth cycles in 2023-2025. Debt and Gilt funds remained stable but scored lower in composite lists due to lower growth.

#### Top 5 Scoring Funds:
1. **Mirae Asset Large Cap Fund - Regular - Growth** (CAGR: 14.81%, Sharpe: 1.760, MDD: -11.27%)
2. **Kotak Flexicap Fund - Regular - Growth** (CAGR: 15.65%, Sharpe: 1.568, MDD: -12.97%)
3. **ICICI Pru Midcap Fund - Regular - Growth** (CAGR: 18.08%, Sharpe: 1.391, MDD: -18.19%)
4. **Mirae Asset Tax Saver Fund - Regular - Growth** (CAGR: 14.95%, Sharpe: 1.468, MDD: -16.40%)
5. **HDFC Mid-Cap Opportunities Fund - Regular - Growth** (CAGR: 16.58%, Sharpe: 1.274, MDD: -16.22%)

#### Bottom 5 Scoring Funds (Performance or Drawdown Challenges):
1. **Axis Small Cap Fund - Regular - Growth** (CAGR: 1.52%, Sharpe: -0.179, MDD: -51.68%)
2. **UTI Mid Cap Fund - Regular - Growth** (CAGR: 1.17%, Sharpe: -0.266, MDD: -28.00%)
3. **SBI Small Cap Fund - Direct Plan - Growth** (CAGR: 2.05%, Sharpe: -0.158, MDD: -52.57%)
4. **HDFC Top 100 Fund - Regular Plan - Growth** (CAGR: 2.64%, Sharpe: -0.231, MDD: -24.73%)
5. **ABSL Small Cap Fund - Regular - Growth** (CAGR: 7.94%, Sharpe: 0.075, MDD: -35.45%)

### C. Investor Demographics & Behavior
* **Age Group Distribution**:
  * **26-35 (Millennials)**: **1,451,600,218.00 INR** (41.2% market share by value)
  * **36-45**: **871,647,528.00 INR** (24.8% market share)
  * **18-25 (Gen Z)**: **531,639,392.00 INR** (15.1% market share)
  * **46-55**: **405,406,469.00 INR** (11.5% market share)
  * **56+ (Retirees)**: **261,286,823.00 INR** (7.4% market share)
* **Geographical Leaders**:
  * **Punjab**: 2,965 transactions totaling **315,780,459.00 INR**
  * **Tamil Nadu**: 2,806 transactions totaling **315,177,237.00 INR**
  * **Madhya Pradesh**: 2,931 transactions totaling **308,312,493.00 INR**
* **Payment Mode Penetration**: 
  * Net Banking: **893.49M INR** (8,250 transactions)
  * Cheque: **892.22M INR** (8,228 transactions)
  * UPI: **888.24M INR** (8,154 transactions)
  * Mandate (Auto-debit): **847.63M INR** (8,146 transactions)
  * *Insight: The digital payment modes (UPI and Net Banking) have reached complete parity with traditional modes (Cheque and Mandate) in volume, reflecting a high financial digitization rate.*

### D. Portfolio Concentration (HHI)
Out of 34 equity funds analyzed:
* **Diversified (< 1,500 HHI)**: **3 funds** (Average HHI: 1,342.56)
* **Moderately Concentrated (1,500 - 2,500 HHI)**: **27 funds** (Average HHI: 2,014.96)
* **Highly Concentrated (> 2,500 HHI)**: **4 funds** (Average HHI: 2,641.02)
  * *Insight: The majority of active equity schemes maintain a moderately concentrated position, focusing on key sectors like Banking (average weight 10.87%, total 62,840 Cr) and IT (average weight 11.39%, total 38,477 Cr).*

### E. Cohort Retention Decay
Tracking quarterly customer cohorts reveals retention behaviors:
* **2024Q1 Cohort (Onboarded in Q1 2024)**: Started with **3,236 investors**.
  * **Q1 (3 Months later)**: **70.92%** active.
  * **Q2 (6 Months later)**: **70.49%** active.
  * **Q4 (12 Months later)**: **69.62%** active.
  * *Insight: This cohort demonstrates highly stable retention, stabilizing near 69% after 1 year.*
* **2024Q2 Cohort**: Started with **971 investors**.
  * **Q1**: **63.13%** active.
  * **Q2**: **63.85%** active.
  * **Q4**: **48.71%** active.
  * *Insight: Mid-year cohorts experience steeper drops, losing over half of their active base by Year 1.*
* **2024Q4 Cohort**: Started with **186 investors**.
  * **Q1**: **40.32%** active.
  * **Q2**: **26.34%** active.
  * *Insight: End-of-year cohorts display a critical churn risk, indicating high drop-offs. Strategic retention should target Q4 onboardings within their first 90 days.*

### F. SIP Continuation Risk Summary
* **Active SIP Investors**: **1,241** (26.1%)
* **At Risk SIP Investors**: **3,521** (73.9%)
  * *Insight: Over 73% of SIP investors have not transacted in the last 35 days relative to the latest data date. This flags a systemic risk in continuous savings plans, suggesting a high number of paused or canceled SIP mandates.*

---

## 8. Interactive Presentation Layer (Dashboard)

The frontend application serves as the visual display for all database tables and analytics:

* **Page 1: Industry Overview**: Displays global KPIs (AUM, SIP Inflows, Folios, Schemes count) and charts detailing the growth of monthly SIP inflows.
* **Page 2: Fund Performance Scorecard**: Displays a searchable and filterable table of composite scores alongside a risk-return scatter chart (CAGR vs. Volatility).
* **Page 3: Drill-Through Analytics**: Renders a popup showing 5-day sampled historical NAV series vs. a rolling Sharpe ratio chart, together with sector holdings tables.
* **Page 4: Investor Demographics**: Visualizes state-by-state heatmaps, age-group pie charts, and payment mode breakdowns.
* **Page 5: Advanced Risk & Cohorts**: Renders heatmap tables for Cohort Retention, lists of at-risk SIP investors, and portfolio HHI concentration gauges.
* **Page 6: Recommendation Engine**: Formulates the top 3 mutual funds matching a user's chosen risk tolerance:

<table style="width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 10px;">
  <colgroup>
    <col style="width: 22%;"/>
    <col style="width: 26%;"/>
    <col style="width: 26%;"/>
    <col style="width: 26%;"/>
  </colgroup>
  <thead>
    <tr>
      <th style="background-color: #2b6cb0; color: #ffffff; padding: 6px; font-size: 8.5pt; font-weight: bold; text-align: left; border: 1px solid #cbd5e0;">Chosen Risk Profile</th>
      <th style="background-color: #2b6cb0; color: #ffffff; padding: 6px; font-size: 8.5pt; font-weight: bold; text-align: left; border: 1px solid #cbd5e0;">Recommended Fund #1</th>
      <th style="background-color: #2b6cb0; color: #ffffff; padding: 6px; font-size: 8.5pt; font-weight: bold; text-align: left; border: 1px solid #cbd5e0;">Recommended Fund #2</th>
      <th style="background-color: #2b6cb0; color: #ffffff; padding: 6px; font-size: 8.5pt; font-weight: bold; text-align: left; border: 1px solid #cbd5e0;">Recommended Fund #3</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="padding: 6px; font-size: 8.5pt; border: 1px solid #cbd5e0;"><strong>Low Risk</strong></td>
      <td style="padding: 6px; font-size: 8.5pt; border: 1px solid #cbd5e0;"><strong>ICICI Pru Liquid Fund - Regular</strong><br/>(Sharpe: 2.506, CAGR: 7.68%)</td>
      <td style="padding: 6px; font-size: 8.5pt; border: 1px solid #cbd5e0;"><strong>Kotak Liquid Fund - Regular</strong><br/>(Sharpe: 1.783, CAGR: 6.18%)</td>
      <td style="padding: 6px; font-size: 8.5pt; border: 1px solid #cbd5e0;"><strong>Mirae Asset Large Cap Fund - Regular</strong><br/>(Sharpe: 1.760, CAGR: 14.81%)</td>
    </tr>
    <tr style="background-color: #f7fafc;">
      <td style="padding: 6px; font-size: 8.5pt; border: 1px solid #cbd5e0;"><strong>Moderate Risk</strong></td>
      <td style="padding: 6px; font-size: 8.5pt; border: 1px solid #cbd5e0;"><strong>Kotak Flexicap Fund - Regular</strong><br/>(Sharpe: 1.568, CAGR: 15.65%)</td>
      <td style="padding: 6px; font-size: 8.5pt; border: 1px solid #cbd5e0;"><strong>Mirae Asset Emerging Bluechip Fund</strong><br/>(Sharpe: 1.070, CAGR: 14.56%)</td>
      <td style="padding: 6px; font-size: 8.5pt; border: 1px solid #cbd5e0;"><strong>UTI Flexi Cap Fund - Regular</strong><br/>(Sharpe: 0.688, CAGR: 15.34%)</td>
    </tr>
    <tr>
      <td style="padding: 6px; font-size: 8.5pt; border: 1px solid #cbd5e0;"><strong>High Risk</strong></td>
      <td style="padding: 6px; font-size: 8.5pt; border: 1px solid #cbd5e0;"><strong>ICICI Pru Midcap Fund - Regular</strong><br/>(Sharpe: 1.391, CAGR: 18.08%)</td>
      <td style="padding: 6px; font-size: 8.5pt; border: 1px solid #cbd5e0;"><strong>DSP Midcap Fund - Regular</strong><br/>(Sharpe: 1.329, CAGR: 17.16%)</td>
      <td style="padding: 6px; font-size: 8.5pt; border: 1px solid #cbd5e0;"><strong>HDFC Mid-Cap Opportunities Fund</strong><br/>(Sharpe: 1.274, CAGR: 16.58%)</td>
    </tr>
  </tbody>
</table>


---

## 9. Verification & Quality Assurance Results

All analytical tables and data pipeline stages have been validated by automated scripts:

```
>>> python verify_pipeline.py
### STARTING PIPELINE VERIFICATION ###
Verifying cleaned files in data/processed:
  - clean_fund_master.csv: [PASS]
  - clean_nav.csv: [PASS]
  - clean_aum.csv: [PASS]
  - clean_sip_inflows.csv: [PASS]
  - clean_category_inflows.csv: [PASS]
  - clean_folio_count.csv: [PASS]
  - clean_performance.csv: [PASS]
  - clean_transactions.csv: [PASS]
  - clean_portfolio_holdings.csv: [PASS]
  - clean_benchmark_indices.csv: [PASS]
  [PASS] All 10 cleaned CSV files are present.

Verifying database bluestock_mf.db:
  [PASS] bluestock_mf.db exists.
  [PASS] All 10 database tables populated with exact row counts.

Granular data quality assertions:
  [PASS] Assert: All NAV values in database are strictly greater than 0.
  [PASS] Assert: All transaction amounts in database are strictly greater than 0.
  [PASS] Assert: KYC status contains only expected values: ['Verified', 'Pending']
  [PASS] Assert: Transaction types contain only expected values: ['SIP', 'Redemption', 'Lumpsum']
  [PASS] Assert: Foreign key reference integrity checks clean.
### PIPELINE VERIFICATION SUCCESSFUL: ALL CHECKS PASSED! ###
```

```
>>> python scripts/verify_analytics.py
### STARTING ANALYTICS VERIFICATION PIPELINE ###
Verifying fact_performance custom metrics:
  [PASS] All 40 funds have computed custom performance metrics.
  - Sharpe range: -0.395 to 2.506
  - Alpha range: -4.19% to 27.46%
  - Max Drawdown range: -52.57% to -0.10%

Verifying fact_advanced_risk:
  [PASS] Advanced risk computed for exactly 40 schemes.
  [PASS] Assert: CVaR is strictly more negative or equal to VaR for all funds.

Verifying fact_rolling_sharpe:
  [PASS] Found 10,600 rolling Sharpe records across 10 top funds.

Verifying fact_cohort_metrics:
  [PASS] Found 21 cohort activity quarters.
  [PASS] Retention percentages lie within bounds: 24.1% to 100.0%

Verifying fact_sip_continuation:
  [PASS] SIP continuation classification counts match (1,241 active vs 3,521 at risk).

Verifying fact_sector_concentration:
  [PASS] HHI indices lie within standard mathematical bounds [100, 10000].

Verifying fact_recommendations:
  [PASS] Engine outputted exactly the top 3 recommended schemes per risk profile.
### ANALYTICS VERIFICATION SUCCESSFUL: ALL CHECKS PASSED! ###
```

---

## 10. Conclusion & Strategic Recommendations

The Mutual Fund Analytics pipeline is complete, verified, and serves a high-performance presentation layer. Based on the insights extracted, we suggest the following strategic initiatives:

1. **Millennial Engagement Focus**: Since investors aged 26-35 represent over 41% of transaction volume (1,451M INR), marketing and mobile features should target digital user experiences, particularly emphasizing fast UPI payment integrations.
2. **Q4 Cohort Retention Push**: Cohorts onboarded in Q4 show high drop-off rates (only 26.34% active by Q2). Trigger automated push notifications, educational newsletters, or loyalty incentives within the first 60 days of onboarding for Q4 users.
3. **Automated SIP Resumption Prompts**: With 73.9% of SIP mandates categorized as **At Risk**, the platform should implement automated triggers. When an investor skips a scheduled SIP contribution (no transaction for 30+ days), the system should suggest a one-click "Resume SIP" or "Pause for 3 Months" rather than letting the mandate lapse.
4. **HHI Concentration Alerts**: Educate investors holding "High Concentration" funds (> 2,500 HHI) on diversification. Recommend supplementary "Diversified" funds (< 1,500 HHI) from the recommendation database to lower their overall portfolio risk.
