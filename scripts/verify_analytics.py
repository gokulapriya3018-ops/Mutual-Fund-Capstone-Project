import os
import sqlite3
import pandas as pd
import numpy as np

def run_verification():
    print("### STARTING ANALYTICS VERIFICATION PIPELINE ###")
    db_file = "bluestock_mf.db"
    
    if not os.path.exists(db_file):
        print(f"[FAIL] Database file {db_file} not found!")
        return
        
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    all_passed = True
    
    # 1. Verify Performance Table Updates
    print("\nVerifying fact_performance custom metrics:")
    cursor.execute("""
        SELECT COUNT(*), COUNT(sharpe_ratio), COUNT(alpha), COUNT(beta), COUNT(max_drawdown_pct)
        FROM fact_performance;
    """)
    cnt, cnt_sharpe, cnt_alpha, cnt_beta, cnt_mdd = cursor.fetchone()
    
    if cnt == 40 and cnt_sharpe == 40 and cnt_alpha == 40 and cnt_beta == 40 and cnt_mdd == 40:
        print("  [PASS] All 40 funds have computed custom performance metrics.")
    else:
        print(f"  [FAIL] Count mismatch in performance metrics: total={cnt}, sharpe={cnt_sharpe}, alpha={cnt_alpha}, beta={cnt_beta}")
        all_passed = False
        
    # Check metric ranges
    cursor.execute("""
        SELECT MIN(sharpe_ratio), MAX(sharpe_ratio), MIN(alpha), MAX(alpha), MIN(max_drawdown_pct), MAX(max_drawdown_pct)
        FROM fact_performance;
    """)
    min_sr, max_sr, min_al, max_al, min_mdd, max_mdd = cursor.fetchone()
    print(f"  - Sharpe range: {min_sr:.3f} to {max_sr:.3f}")
    print(f"  - Alpha range: {min_al:.2f}% to {max_al:.2f}%")
    print(f"  - Max Drawdown range: {min_mdd:.2f}% to {max_mdd:.2f}%")
    
    if min_mdd < -50 or max_mdd > 0:
        print("  [WARNING] Drawdowns out of typical bounds (should be negative and above -100%).")
    else:
        print("  [PASS] Drawdown bounds look correct.")

    # 2. Verify Advanced Risk Metrics (VaR & CVaR)
    print("\nVerifying fact_advanced_risk:")
    cursor.execute("SELECT COUNT(*) FROM fact_advanced_risk;")
    cnt_risk = cursor.fetchone()[0]
    if cnt_risk == 40:
        print("  [PASS] Advanced risk computed for exactly 40 schemes.")
    else:
        print(f"  [FAIL] Advanced risk count mismatch: {cnt_risk}")
        all_passed = False
        
    # Check VaR vs CVaR property: CVaR is expected to be more negative/equal to VaR
    cursor.execute("SELECT COUNT(*) FROM fact_advanced_risk WHERE cvar_95_pct > var_95_pct;")
    bad_risk_relation = cursor.fetchone()[0]
    if bad_risk_relation == 0:
        print("  [PASS] Assert: CVaR is strictly more negative or equal to VaR for all funds.")
    else:
        print(f"  [FAIL] Found {bad_risk_relation} records where CVaR was less negative than VaR!")
        all_passed = False

    # 3. Verify Rolling Sharpe
    print("\nVerifying fact_rolling_sharpe:")
    cursor.execute("SELECT COUNT(*), COUNT(DISTINCT amfi_code) FROM fact_rolling_sharpe;")
    cnt_rs, cnt_rs_funds = cursor.fetchone()
    if cnt_rs > 5000 and cnt_rs_funds == 10:
        print(f"  [PASS] Found {cnt_rs} rolling Sharpe records across {cnt_rs_funds} top funds.")
    else:
        print(f"  [FAIL] Rolling Sharpe count mismatch: records={cnt_rs}, funds={cnt_rs_funds}")
        all_passed = False

    # 4. Verify Cohorts
    print("\nVerifying fact_cohort_metrics:")
    cursor.execute("SELECT COUNT(*) FROM fact_cohort_metrics;")
    cnt_cohorts = cursor.fetchone()[0]
    if cnt_cohorts > 10:
        print(f"  [PASS] Found {cnt_cohorts} cohort activity quarters.")
    else:
        print(f"  [FAIL] Cohort records missing or sparse: {cnt_cohorts}")
        all_passed = False
        
    cursor.execute("SELECT MIN(retention_pct), MAX(retention_pct) FROM fact_cohort_metrics;")
    min_ret, max_ret = cursor.fetchone()
    if min_ret >= 0.0 and max_ret <= 100.001:
        print(f"  [PASS] Retention percentages lie within bounds: {min_ret:.1f}% to {max_ret:.1f}%")
    else:
        print(f"  [FAIL] Invalid retention percentage found: min={min_ret}, max={max_ret}")
        all_passed = False

    # 5. Verify SIP Continuation
    print("\nVerifying fact_sip_continuation:")
    cursor.execute("SELECT COUNT(*), COUNT(CASE WHEN status='Active' THEN 1 END), COUNT(CASE WHEN status='At Risk' THEN 1 END) FROM fact_sip_continuation;")
    total_sip, active_sip, at_risk_sip = cursor.fetchone()
    print(f"  - Total unique SIP investors: {total_sip}")
    print(f"  - Active SIPs: {active_sip}")
    print(f"  - At Risk SIPs: {at_risk_sip}")
    
    if total_sip > 0 and (active_sip + at_risk_sip == total_sip):
        print("  [PASS] SIP continuation classification counts match.")
    else:
        print("  [FAIL] Classification count mismatch in SIP continuation table.")
        all_passed = False

    # 6. Verify HHI Sector Concentration
    print("\nVerifying fact_sector_concentration:")
    cursor.execute("SELECT COUNT(*), MIN(hhi_index), MAX(hhi_index) FROM fact_sector_concentration;")
    cnt_hhi, min_hhi, max_hhi = cursor.fetchone()
    print(f"  - Portfolios with HHI: {cnt_hhi}")
    print(f"  - HHI Index range: {min_hhi:.1f} to {max_hhi:.1f}")
    
    if cnt_hhi > 0 and min_hhi >= 100 and max_hhi <= 10000:
        print("  [PASS] HHI indices lie within standard mathematical bounds [100, 10000].")
    else:
        print("  [FAIL] HHI metrics are invalid or out of bounds.")
        all_passed = False

    # 7. Verify Recommendations
    print("\nVerifying fact_recommendations:")
    cursor.execute("SELECT DISTINCT risk_profile, COUNT(*) FROM fact_recommendations GROUP BY risk_profile;")
    reco_counts = cursor.fetchall()
    print(f"  - Recommendations by profile: {reco_counts}")
    
    expected_recos = [('High Risk', 3), ('Low Risk', 3), ('Moderate Risk', 3)]
    if set(reco_counts) == set(expected_recos):
        print("  [PASS] Engine outputted exactly the top 3 recommended schemes per risk profile.")
    else:
        print(f"  [FAIL] Recommendations mismatch: expected {expected_recos}, found {reco_counts}")
        all_passed = False
        
    conn.close()
    
    if all_passed:
        print("\n### ANALYTICS VERIFICATION SUCCESSFUL: ALL CHECKS PASSED! ###")
    else:
        print("\n### ANALYTICS VERIFICATION FAILED: SOME CHECKS MISSED! ###")

if __name__ == "__main__":
    run_verification()
