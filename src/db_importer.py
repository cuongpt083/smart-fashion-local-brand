"""
Backward-compatibility wrapper for src.db.importer
"""
import argparse
from src.db.importer import import_all_csv_to_sqlite

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import/Upsert CSV data into SQLite3")
    parser.add_argument("--csv-dir", type=str, default="data/csv", help="Directory containing CSV files")
    parser.add_argument("--db-path", type=str, default="data/smart_fashion.db", help="Target SQLite3 database file path")
    args = parser.parse_args()
    
    import_all_csv_to_sqlite(args.csv_dir, args.db_path)
