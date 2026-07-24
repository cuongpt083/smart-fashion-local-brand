import os
import sqlite3
import pandas as pd
from .schema import create_tables

def upsert_table_from_csv(conn, table_name, csv_path):
    if not os.path.exists(csv_path):
        return 0

    df = pd.read_csv(csv_path)
    if df.empty:
        return 0

    cursor = conn.cursor()
    columns = list(df.columns)
    placeholders = ", ".join(["?"] * len(columns))
    col_names = ", ".join(columns)
    
    sql = f"INSERT OR REPLACE INTO {table_name} ({col_names}) VALUES ({placeholders})"
    
    data_tuples = [tuple(x) for x in df.to_numpy()]
    cursor.executemany(sql, data_tuples)
    conn.commit()
    
    return len(df)

def import_all_csv_to_sqlite(csv_dir="data/csv", db_path="data/smart_fashion.db"):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    create_tables(conn)
    
    tables = [
        "DIM_PRODUCTS",
        "DIM_CUSTOMERS",
        "DIM_EMPLOYEE",
        "FACT_INVOICES",
        "FACT_INVOICES_LINES",
        "FACT_ORDERS",
        "FACT_ORDERS_LINES"
    ]
    
    summary = {}
    for tbl in tables:
        csv_file = os.path.join(csv_dir, f"{tbl}.csv")
        count = upsert_table_from_csv(conn, tbl, csv_file)
        summary[tbl] = count
        
    conn.close()
    return summary
