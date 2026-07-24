import pandas as pd
import numpy as np
import random
from datetime import datetime

def format_invoice_code(index: int) -> str:
    """Rule R1: Format invoice code with HDIP prefix and 6-digit padded index."""
    return f"HDIP{index:06d}"

def format_order_code(index: int) -> str:
    """Rule R1: Format order code with DH prefix and 6-digit padded index."""
    return f"DH{index:06d}"

def apply_rule_r2_inventory_backfill(df_products: pd.DataFrame, df_invoice_lines: pd.DataFrame, df_order_lines: pd.DataFrame = None) -> pd.DataFrame:
    """
    Rule R2 (Iterative Back-filling):
    Ensures stock_on_hand >= sum(quantity_sold) + safety_stock for every SKU in DIM_PRODUCTS.
    """
    inv_sold = df_invoice_lines.groupby('product_code')['quantity'].sum().to_dict() if df_invoice_lines is not None and not df_invoice_lines.empty else {}
    ord_sold = df_order_lines.groupby('product_code')['quantity'].sum().to_dict() if df_order_lines is not None and not df_order_lines.empty else {}
    
    df_prod = df_products.copy()
    updated_stock = []
    
    for idx, row in df_prod.iterrows():
        p_code = row['product_code']
        total_sold = inv_sold.get(p_code, 0) + ord_sold.get(p_code, 0)
        safety_stock = random.randint(15, 60)
        updated_stock.append(int(total_sold + safety_stock))
        
    df_prod['stock_on_hand'] = updated_stock
    return df_prod

def apply_customer_metrics_backfill(df_customers: pd.DataFrame, df_invoices: pd.DataFrame) -> pd.DataFrame:
    """
    Business Rule: Update total_sales and last_transaction_date in DIM_CUSTOMERS
    based on actual generated transactions in FACT_INVOICES.
    """
    if df_invoices is None or df_invoices.empty:
        return df_customers

    df_cust = df_customers.copy()
    
    # Calculate sum of invoice total_amount per customer
    cust_sales = df_invoices.groupby('customer_code')['total_amount'].sum().to_dict()
    
    # Calculate latest transaction date per customer
    df_inv_dt = df_invoices.copy()
    df_inv_dt['order_created_at'] = pd.to_datetime(df_inv_dt['order_created_at'])
    cust_last_dt = df_inv_dt.groupby('customer_code')['order_created_at'].max().to_dict()
    
    total_sales_list = []
    last_dt_list = []
    
    for idx, row in df_cust.iterrows():
        c_code = row['customer_code']
        sales = cust_sales.get(c_code, 0.0)
        last_dt = cust_last_dt.get(c_code, None)
        
        total_sales_list.append(round(sales, 0))
        if pd.notnull(last_dt):
            last_dt_list.append(last_dt.strftime('%Y-%m-%d %H:%M:%S'))
        else:
            last_dt_list.append('')
            
    df_cust['total_sales'] = total_sales_list
    df_cust['last_transaction_date'] = last_dt_list
    return df_cust

def validate_financial_mathematical_logic(df_invoices: pd.DataFrame, df_invoice_lines: pd.DataFrame) -> bool:
    """
    Validation Rule A: Checks that total_amount of each invoice equals SUM(line_total) of its invoice lines.
    And line_total == (quantity * unit_price) - line_discount_amount.
    """
    # Check line total calculation
    calculated_line_totals = (df_invoice_lines['quantity'] * df_invoice_lines['unit_price']) - df_invoice_lines['line_discount_amount']
    line_check = np.allclose(df_invoice_lines['line_total'], calculated_line_totals)
    
    # Check invoice header sum
    line_sums = df_invoice_lines.groupby('invoice_code')['line_total'].sum().to_dict()
    inv_check = True
    for idx, row in df_invoices.iterrows():
        expected_sum = line_sums.get(row['invoice_code'], 0.0)
        if not np.isclose(row['total_amount'], expected_sum):
            inv_check = False
            break
            
    return line_check and inv_check
