import random

def format_invoice_code(index: int) -> str:
    """Rule R1: Format invoice code with HDIP prefix."""
    return f"HDIP{index:06d}"

def format_order_code(index: int) -> str:
    return f"DH{index:06d}"

def apply_rule_r2_inventory_backfill(df_products, df_invoice_lines, df_order_lines=None):
    """
    Rule R2 (Iterative Back-filling):
    Calculates total sold quantity per product from invoice lines (and order lines)
    and updates stock_on_hand in DIM_PRODUCTS so that stock_on_hand >= sold_qty + safety_buffer.
    """
    inv_sold = df_invoice_lines.groupby('product_code')['quantity'].sum().to_dict()
    ord_sold = {}
    if df_order_lines is not None and not df_order_lines.empty:
        ord_sold = df_order_lines.groupby('product_code')['quantity'].sum().to_dict()
        
    updated_products = []
    for idx, row in df_products.iterrows():
        p_code = row['product_code']
        total_sold = inv_sold.get(p_code, 0) + ord_sold.get(p_code, 0)
        safety_stock = random.randint(15, 60)
        row['stock_on_hand'] = total_sold + safety_stock
        updated_products.append(row)
        
    return df_products.__class__(updated_products)
