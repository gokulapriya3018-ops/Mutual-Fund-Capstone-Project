import os
import http.server
import socketserver
import json
import sqlite3
from urllib.parse import urlparse, parse_qs

PORT = 8050
DB_FILE = "bluestock_mf.db"

class DashboardAPIHandler(http.server.SimpleHTTPRequestHandler):
    def get_db_connection(self):
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)

        # Route ping requests to keep server awake
        if path == "/ping":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "message": "pong"}).encode("utf-8"))
            return

        # Route API requests
        if path.startswith("/api/"):
            self.handle_api(path, query_params)
        else:
            # Fallback to serving static files
            # Serve index.html if pointing to root or directories
            if path == "/" or path == "/dashboard" or path == "/dashboard/":
                self.path = "/dashboard/index.html"
            else:
                self.path = "/dashboard" + path
            
            # Prevent directory traversal (compatible with both Windows and Linux slashes)
            normalized_path = os.path.normpath(self.path)
            clean_path = normalized_path.lstrip("/\\")
            if not clean_path.startswith("dashboard"):
                self.send_error(403, "Access Denied")
                return
                
            super().do_GET()

    def handle_api(self, path, params):
        # Extract filters
        category_filter = params.get("category", [None])[0]
        amc_filter = params.get("fund_house", [None])[0]

        # Connect to db
        conn = self.get_db_connection()
        cursor = conn.cursor()

        response_data = None
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        try:
            if path == "/api/filters":
                # Get unique categories and fund houses
                cursor.execute("SELECT DISTINCT category FROM dim_fund WHERE category IS NOT NULL ORDER BY category;")
                categories = [r[0] for r in cursor.fetchall()]
                cursor.execute("SELECT DISTINCT fund_house FROM dim_fund WHERE fund_house IS NOT NULL ORDER BY fund_house;")
                amcs = [r[0] for r in cursor.fetchall()]
                response_data = {"categories": categories, "fund_houses": amcs}

            elif path == "/api/kpis":
                # Build filtered where clause
                where_clauses = []
                args = []
                if category_filter:
                    where_clauses.append("category = ?")
                    args.append(category_filter)
                if amc_filter:
                    where_clauses.append("fund_house = ?")
                    args.append(amc_filter)
                
                where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

                # Total AUM
                cursor.execute(f"SELECT SUM(aum_crore) FROM fact_performance {where_sql};", args)
                total_aum = cursor.fetchone()[0] or 0.0

                # Schemes Count
                cursor.execute(f"SELECT COUNT(*) FROM dim_fund {where_sql};", args)
                schemes_cnt = cursor.fetchone()[0] or 0

                # Latest SIP Inflow
                cursor.execute("SELECT sip_inflow_crore, month FROM fact_sip_inflows ORDER BY month DESC LIMIT 1;")
                sip_row = cursor.fetchone()
                latest_sip_inflow = sip_row[0] if sip_row else 0.0
                latest_sip_month = sip_row[1] if sip_row else "N/A"

                # Latest Folio Count
                cursor.execute("SELECT total_folios_crore, month FROM dim_industry_folio ORDER BY month DESC LIMIT 1;")
                folio_row = cursor.fetchone()
                latest_folios = folio_row[0] if folio_row else 0.0

                response_data = {
                    "total_aum_crore": round(total_aum, 2),
                    "total_schemes": schemes_cnt,
                    "latest_sip_inflow_crore": latest_sip_inflow,
                    "latest_sip_month": latest_sip_month,
                    "latest_industry_folios_crore": latest_folios
                }

            elif path == "/api/performance":
                where_clauses = []
                args = []
                if category_filter:
                    where_clauses.append("p.category = ?")
                    args.append(category_filter)
                if amc_filter:
                    where_clauses.append("p.fund_house = ?")
                    args.append(amc_filter)
                
                where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

                # Scorecard query joining advanced risk metrics
                sql = f"""
                    SELECT p.*, r.var_95_pct, r.cvar_95_pct, h.hhi_index, h.concentration_level
                    FROM fact_performance p
                    LEFT JOIN fact_advanced_risk r ON p.amfi_code = r.amfi_code
                    LEFT JOIN fact_sector_concentration h ON p.amfi_code = h.amfi_code
                    {where_sql}
                    ORDER BY p.sharpe_ratio DESC;
                """
                cursor.execute(sql, args)
                rows = cursor.fetchall()
                
                # Convert rows to dicts
                response_data = [dict(row) for row in rows]

            elif path == "/api/demographics":
                # Demographic patterns of transactions
                # Join transaction details filtered by category or fund house
                where_clauses = []
                args = []
                if category_filter:
                    where_clauses.append("f.category = ?")
                    args.append(category_filter)
                if amc_filter:
                    where_clauses.append("f.fund_house = ?")
                    args.append(amc_filter)
                
                where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

                # Age & Gender
                cursor.execute(f"""
                    SELECT age_group, gender, COUNT(*) as count, SUM(amount_inr) as amount
                    FROM fact_transactions t
                    JOIN dim_fund f ON t.amfi_code = f.amfi_code
                    {where_sql}
                    GROUP BY age_group, gender;
                """, args)
                age_gender = [dict(r) for r in cursor.fetchall()]

                # State-wise
                cursor.execute(f"""
                    SELECT state, SUM(amount_inr) as amount, COUNT(*) as count
                    FROM fact_transactions t
                    JOIN dim_fund f ON t.amfi_code = f.amfi_code
                    {where_sql}
                    GROUP BY state
                    ORDER BY amount DESC;
                """, args)
                state_data = [dict(r) for r in cursor.fetchall()]

                # Payment Mode
                cursor.execute(f"""
                    SELECT payment_mode, COUNT(*) as count, SUM(amount_inr) as amount
                    FROM fact_transactions t
                    JOIN dim_fund f ON t.amfi_code = f.amfi_code
                    {where_sql}
                    GROUP BY payment_mode;
                """, args)
                payment_mode = [dict(r) for r in cursor.fetchall()]

                response_data = {
                    "age_gender": age_gender,
                    "state_wise": state_data,
                    "payment_mode": payment_mode
                }

            elif path == "/api/market-trends":
                # Industry SIP growth, category net flows, folio trends
                cursor.execute("SELECT month, sip_inflow_crore, active_sip_accounts_crore, new_sip_accounts_lakh, sip_aum_lakh_crore FROM fact_sip_inflows ORDER BY month;")
                sip_inflows = [dict(r) for r in cursor.fetchall()]

                cursor.execute("SELECT month, category, net_inflow_crore FROM fact_category_inflows ORDER BY month, category;")
                cat_inflows = [dict(r) for r in cursor.fetchall()]

                cursor.execute("SELECT month, total_folios_crore, equity_folios_crore, debt_folios_crore, hybrid_folios_crore FROM dim_industry_folio ORDER BY month;")
                folio_counts = [dict(r) for r in cursor.fetchall()]

                response_data = {
                    "sip_inflows": sip_inflows,
                    "category_inflows": cat_inflows,
                    "folio_trends": folio_counts
                }

            elif path == "/api/recommendations":
                risk_profile = params.get("risk_profile", ["Low Risk"])[0]
                cursor.execute("""
                    SELECT r.*, f.fund_house, f.risk_category, f.expense_ratio_pct
                    FROM fact_recommendations r
                    JOIN dim_fund f ON r.amfi_code = f.amfi_code
                    WHERE r.risk_profile = ?
                    ORDER BY r.rank;
                """, (risk_profile,))
                response_data = [dict(r) for r in cursor.fetchall()]

            elif path == "/api/advanced-risk":
                where_clauses = []
                args = []
                if category_filter:
                    where_clauses.append("f.category = ?")
                    args.append(category_filter)
                if amc_filter:
                    where_clauses.append("f.fund_house = ?")
                    args.append(amc_filter)
                where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

                # Sector Concentration HHI
                cursor.execute(f"""
                    SELECT sc.amfi_code, sc.scheme_name, sc.hhi_index, sc.concentration_level, f.category
                    FROM fact_sector_concentration sc
                    JOIN dim_fund f ON sc.amfi_code = f.amfi_code
                    {where_sql}
                    ORDER BY sc.hhi_index DESC;
                """, args)
                hhi_data = [dict(r) for r in cursor.fetchall()]

                # Top At Risk SIPs
                cursor.execute("""
                    SELECT sc.investor_id, sc.last_transaction_date, sc.days_since_last_tx, sc.status
                    FROM fact_sip_continuation sc
                    WHERE sc.status = 'At Risk'
                    ORDER BY sc.days_since_last_tx DESC
                    LIMIT 20;
                """)
                sip_continuation = [dict(r) for r in cursor.fetchall()]

                # Cohort Retention table
                cursor.execute("SELECT * FROM fact_cohort_metrics ORDER BY cohort_quarter, quarter_index;")
                cohorts = [dict(r) for r in cursor.fetchall()]

                response_data = {
                    "hhi_concentration": hhi_data,
                    "sip_at_risk": sip_continuation,
                    "cohorts": cohorts
                }

            elif path == "/api/fund-details":
                amfi_code = params.get("amfi_code", [None])[0]
                if not amfi_code:
                    response_data = {"error": "AMFI code required"}
                else:
                    # Fund information
                    cursor.execute("SELECT * FROM dim_fund WHERE amfi_code = ?;", (amfi_code,))
                    fund_info = dict(cursor.fetchone()) if cursor.rowcount != 0 else {}
                    
                    # Performance metrics
                    cursor.execute("""
                        SELECT p.*, r.var_95_pct, r.cvar_95_pct, h.hhi_index, h.concentration_level 
                        FROM fact_performance p
                        LEFT JOIN fact_advanced_risk r ON p.amfi_code = r.amfi_code
                        LEFT JOIN fact_sector_concentration h ON p.amfi_code = h.amfi_code
                        WHERE p.amfi_code = ?;
                    """, (amfi_code,))
                    row = cursor.fetchone()
                    perf_info = dict(row) if row else {}

                    # Stock holdings weights
                    cursor.execute("""
                        SELECT stock_name, stock_symbol, sector, weight_pct, market_value_cr
                        FROM fact_portfolio_holdings
                        WHERE amfi_code = ?
                        ORDER BY weight_pct DESC;
                    """, (amfi_code,))
                    holdings = [dict(r) for r in cursor.fetchall()]

                    # Historical NAV series (Sub-sampled for graph speed: 1 point every week/5 days)
                    cursor.execute("""
                        SELECT nav_date, nav, daily_return 
                        FROM fact_nav 
                        WHERE amfi_code = ? 
                        ORDER BY nav_date;
                    """, (amfi_code,))
                    nav_history = [dict(r) for r in cursor.fetchall()]

                    # Rolling Sharpe series
                    cursor.execute("""
                        SELECT nav_date, rolling_sharpe
                        FROM fact_rolling_sharpe
                        WHERE amfi_code = ?
                        ORDER BY nav_date;
                    """, (amfi_code,))
                    rolling_sharpe = [dict(r) for r in cursor.fetchall()]

                    response_data = {
                        "fund": fund_info,
                        "performance": perf_info,
                        "holdings": holdings,
                        "nav_history": nav_history[::5],  # Sample every 5th business day
                        "rolling_sharpe": rolling_sharpe[::5]
                    }

            else:
                self.send_error(404, "API Endpoint Not Found")
                conn.close()
                return

            self.wfile.write(json.dumps(response_data).encode("utf-8"))

        except Exception as e:
            # Handle error
            print(f"Error handling API path {path}: {str(e)}")
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

        conn.close()

def main():
    # Make sure we run in the correct working directory containing the database
    handler = DashboardAPIHandler
    # Enable socket re-use to avoid port-binding issues on restarts
    socketserver.TCPServer.allow_reuse_address = True
    
    # Read port from environment variable for cloud deployment compatibility
    env_port = int(os.environ.get("PORT", PORT))
    
    with socketserver.TCPServer(("0.0.0.0", env_port), handler) as httpd:
        print(f"Server serving at port {env_port}")
        print(f"To open the dashboard, open browser at http://localhost:{env_port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.shutdown()

if __name__ == "__main__":
    main()
