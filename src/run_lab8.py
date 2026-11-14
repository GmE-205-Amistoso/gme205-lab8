import json
from pathlib import Path

from database import check_connection, fetch_parcels_by_land_use
from exchange import build_feature_collection, validate_feature_collection

OUTPUT_PATH = Path("output/")

def main():
    # 1. Confirm Python can reach PostgreSQL/PostGIS.
        if not check_connection():
            return
    
        # 2. Retrieve selected database rows.
        rows = fetch_parcels_by_land_use("Residential")
        print("Rows returned:", len(rows))
    
        if rows:
            print("First database row:", rows[0])

if __name__ == "__main__":
    main()