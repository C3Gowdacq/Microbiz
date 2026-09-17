import os
import sys
import pandas as pd

def resolve_file_path(base_dir, relative_path):
    """
    Resolve file path, allowing for 'rossman' folder as a fallback for 'rossmann'.
    """
    primary_path = os.path.join(base_dir, relative_path)
    if os.path.exists(primary_path):
        return primary_path, relative_path
    
    # Check alternate folder name 'rossman' for 'rossmann'
    if relative_path.startswith("rossmann/"):
        alt_relative = relative_path.replace("rossmann/", "rossman/", 1)
        alt_path = os.path.join(base_dir, alt_relative)
        if os.path.exists(alt_path):
            return alt_path, alt_relative
            
    return None, relative_path

def main():
    raw_dir = os.path.join("ml", "data", "raw")
    
    expected_files = [
        "rossmann/train.csv",
        "rossmann/test.csv",
        "rossmann/store.csv",
        "online_retail_ii/online_retail_II.csv",
        "superstore/Sample - Superstore.csv"
    ]
    
    expected_columns = {
        "rossmann/train.csv": [
            "Store", "DayOfWeek", "Date", "Sales", "Customers", "Open", "Promo", "StateHoliday", "SchoolHoliday"
        ],
        "rossmann/store.csv": [
            "Store", "StoreType", "Assortment", "CompetitionDistance", "CompetitionOpenSinceMonth",
            "CompetitionOpenSinceYear", "Promo2", "Promo2SinceWeek", "Promo2SinceYear", "PromoInterval"
        ],
        "online_retail_ii/online_retail_II.csv": [
            "Invoice", "StockCode", "Description", "Quantity", "InvoiceDate", "Price", "Customer ID", "Country"
        ],
        "superstore/Sample - Superstore.csv": [
            "Order Date", "Ship Date", "Customer ID", "Sales", "Profit", "Discount", "Category", "Sub-Category", "Quantity"
        ]
    }

    print("==================================================")
    print("STEP 1: Checking Raw Dataset File Existence")
    print("==================================================")
    
    resolved_paths = {}
    missing_files = []
    
    for rel_path in expected_files:
        full_path, actual_rel = resolve_file_path(raw_dir, rel_path)
        if full_path:
            resolved_paths[rel_path] = (full_path, actual_rel)
            print(f"[FOUND] {rel_path} -> ({full_path})")
        else:
            missing_files.append(rel_path)
            print(f"[MISSING] {rel_path}")

    if missing_files:
        print("\n" + "=" * 50)
        print("ERROR: Missing raw dataset files:")
        for missing in missing_files:
            print(f"  - ml/data/raw/{missing}")
        print("Stopping execution as requested.")
        print("=" * 50)
        sys.exit(1)

    print("\nAll required files found! Proceeding with data inspection...\n")

    summary_data = []

    # Process each file
    for rel_path in expected_files:
        full_path, actual_rel = resolved_paths[rel_path]
        print("=" * 70)
        print(f"INSPECTING: {rel_path} (actual path: {full_path})")
        print("=" * 70)
        
        # Determine encoding and load dataframe
        df = None
        encoding_used = "utf-8"
        
        if "online_retail_II.csv" in rel_path:
            try:
                df = pd.read_csv(full_path, encoding="utf-8")
                encoding_used = "utf-8"
            except (UnicodeDecodeError, pd.errors.ParserError):
                df = pd.read_csv(full_path, encoding="ISO-8859-1")
                encoding_used = "ISO-8859-1"
            print(f"Encoding Used: {encoding_used}")
        else:
            try:
                df = pd.read_csv(full_path, encoding="utf-8")
                encoding_used = "utf-8"
            except UnicodeDecodeError:
                df = pd.read_csv(full_path, encoding="ISO-8859-1")
                encoding_used = "ISO-8859-1"
            print(f"Encoding Used: {encoding_used}")

        rows, cols = df.shape
        print(f"Shape: {rows} rows, {cols} columns")
        
        print("\n--- Column Names & Data Types ---")
        print(df.dtypes)
        
        print("\n--- First 3 Rows ---")
        print(df.head(3))
        
        print("\n--- Null Values Count Per Column ---")
        print(df.isnull().sum())
        
        # Column Sanity Check
        ready = True
        if rel_path in expected_columns:
            exp_cols = expected_columns[rel_path]
            actual_cols = list(df.columns)
            missing_cols = [col for col in exp_cols if col not in actual_cols]
            
            print("\n--- Column Sanity Check ---")
            if not missing_cols:
                print("PASSED: All expected columns are present.")
            else:
                ready = False
                print("FAILED: Missing expected columns:")
                for mc in missing_cols:
                    print(f"  - Missing: {mc}")
                print("\nActual Columns in File:")
                print(actual_cols)
        else:
            print("\n--- Column Sanity Check ---")
            print("INFO: No explicit column list defined for this file (structural verification passed).")

        summary_data.append({
            "Dataset": rel_path,
            "Found?": "Yes",
            "Rows": rows,
            "Columns": cols,
            "Ready for preprocessing?": "Yes" if ready else "No"
        })
        print("\n")

    # Print Summary Table
    print("=" * 80)
    print("SUMMARY TABLE")
    print("=" * 80)
    summary_df = pd.DataFrame(summary_data)
    print(f"| {' | '.join(summary_df.columns)} |")
    print(f"| {' | '.join(['---'] * len(summary_df.columns))} |")
    for _, row in summary_df.iterrows():
        print(f"| {' | '.join([str(val) for val in row.values])} |")
    print("=" * 80)

if __name__ == "__main__":
    main()

