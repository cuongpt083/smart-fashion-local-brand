import sys
import os
import argparse
from src.sdv.generator import generate_all_synthetic_data
from src.db.importer import import_all_csv_to_sqlite

def run_pipeline(products=120, invoices=1500, customers=350, csv_dir="data/csv", db_path="data/smart_fashion.db"):
    print("============================================================")
    print("   SMART FASHION LOCAL BRAND - DATA GENERATION & DB PIPELINE")
    print("============================================================")
    
    print("\n[Bước 1/2] Thực thi Module SDV (src.sdv) sinh dữ liệu giả lập CSV...")
    results = generate_all_synthetic_data(
        num_products=products,
        num_invoices=invoices,
        num_customers=customers,
        output_dir=csv_dir
    )
    print(f"✅ Đã sinh thành công {len(results['DIM_PRODUCTS'])} SKU sản phẩm và {len(results['FACT_INVOICES'])} hóa đơn!")
    
    print("\n[Bước 2/2] Thực thi Module Database (src.db) Import/Upsert vào SQLite3...")
    summary = import_all_csv_to_sqlite(csv_dir=csv_dir, db_path=db_path)
    for tbl, count in summary.items():
        print(f"   - {tbl}: {count} bản ghi")
        
    print("\n============================================================")
    print("🎉 HOÀN THÀNH TOÀN BỘ PIPELINE THÀNH CÔNG!")
    print(f"   Dữ liệu SQLite3 sẵn sàng tại: {os.path.abspath(db_path)}")
    print("============================================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Full Synthetic Data Pipeline CLI")
    parser.add_argument("--products", type=int, default=120, help="Minimum products count")
    parser.add_argument("--invoices", type=int, default=1500, help="Minimum invoices count")
    parser.add_argument("--customers", type=int, default=350, help="Customers count")
    parser.add_argument("--csv-dir", type=str, default="data/csv", help="CSV folder")
    parser.add_argument("--db-path", type=str, default="data/smart_fashion.db", help="SQLite database path")
    args = parser.parse_args()
    
    run_pipeline(
        products=args.products,
        invoices=args.invoices,
        customers=args.customers,
        csv_dir=args.csv_dir,
        db_path=args.db_path
    )
