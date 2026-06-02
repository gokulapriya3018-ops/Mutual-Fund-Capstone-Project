import os
import requests
import pandas as pd
import time

def fetch_scheme_nav(scheme_code):
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    print(f"Fetching NAV data for scheme code: {scheme_code} from {url}...")
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        json_data = response.json()
        
        # Check if 'meta' and 'data' are present
        if not json_data or "meta" not in json_data or "data" not in json_data:
            print(f"Error: Invalid or empty JSON response for scheme code {scheme_code}")
            return None
        
        meta = json_data["meta"]
        data = json_data["data"]
        
        # Log metadata information
        scheme_name = meta.get("scheme_name", "Unknown Scheme")
        fund_house = meta.get("fund_house", "Unknown Fund House")
        print(f"Successfully fetched details for: {scheme_name} ({fund_house})")
        
        # Create DataFrame
        df = pd.DataFrame(data)
        if df.empty:
            print(f"Warning: No NAV data found for scheme code {scheme_code}")
            return None
        
        # Add metadata fields to each row for tracking
        df["scheme_code"] = scheme_code
        df["scheme_name"] = scheme_name
        df["fund_house"] = fund_house
        df["scheme_category"] = meta.get("scheme_category", "")
        df["scheme_type"] = meta.get("scheme_type", "")
        
        # Reorder columns
        cols = ["scheme_code", "scheme_name", "date", "nav", "fund_house", "scheme_category", "scheme_type"]
        df = df[cols]
        
        return df
    except Exception as e:
        print(f"Error fetching scheme code {scheme_code}: {e}")
        return None

def main():
    schemes = {
        "125497": "HDFC Top 100 Direct",
        "119551": "SBI Bluechip",
        "120503": "ICICI Bluechip",
        "118632": "Nippon Large Cap",
        "119092": "Axis Bluechip",
        "120841": "Kotak Bluechip"
    }
    
    output_dir = os.path.join("data", "raw")
    os.makedirs(output_dir, exist_ok=True)
    
    for code, name in schemes.items():
        df = fetch_scheme_nav(code)
        if df is not None:
            output_file = os.path.join(output_dir, f"{code}_nav.csv")
            df.to_csv(output_file, index=False)
            print(f"Saved {len(df)} NAV records for scheme {code} ({name}) to {output_file}")
        else:
            print(f"Failed to fetch or save NAV history for scheme {code} ({name})")
        
        # Brief sleep between API requests to be polite to the API
        time.sleep(1)

if __name__ == "__main__":
    main()
