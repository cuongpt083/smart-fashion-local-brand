import os
import argparse
import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta

from .constraints import (
    format_invoice_code,
    format_order_code,
    apply_rule_r2_inventory_backfill,
    apply_customer_metrics_backfill,
    validate_financial_mathematical_logic
)

fake = Faker('vi_VN')
Faker.seed(42)
np.random.seed(42)
random.seed(42)

def create_sdv_metadata():
    """
    Tạo SDV MultiTableMetadata mô hình hóa quan hệ Cha-Con (Parent-Child FK)
    cho 7 bảng KiotViet Data Warehouse.
    """
    try:
        from sdv.metadata import MultiTableMetadata
        metadata = MultiTableMetadata()
        
        # Add Tables
        metadata.add_table('DIM_PRODUCTS', primary_key='product_code')
        metadata.add_table('DIM_CUSTOMERS', primary_key='customer_code')
        metadata.add_table('DIM_EMPLOYEE', primary_key='employee_code')
        metadata.add_table('FACT_INVOICES', primary_key='invoice_code')
        metadata.add_table('FACT_INVOICES_LINES', primary_key='invoice_line_id')
        metadata.add_table('FACT_ORDERS', primary_key='order_code')
        metadata.add_table('FACT_ORDERS_LINES', primary_key='order_line_id')
        
        # Add Relationships (Parent -> Child FKs)
        metadata.add_relationship(parent_table_name='DIM_CUSTOMERS', child_table_name='FACT_INVOICES', foreign_key='customer_code')
        metadata.add_relationship(parent_table_name='DIM_EMPLOYEE', child_table_name='FACT_INVOICES', foreign_key='employee_code')
        metadata.add_relationship(parent_table_name='FACT_INVOICES', child_table_name='FACT_INVOICES_LINES', foreign_key='invoice_code')
        metadata.add_relationship(parent_table_name='DIM_PRODUCTS', child_table_name='FACT_INVOICES_LINES', foreign_key='product_code')

        metadata.add_relationship(parent_table_name='DIM_CUSTOMERS', child_table_name='FACT_ORDERS', foreign_key='customer_code')
        metadata.add_relationship(parent_table_name='DIM_EMPLOYEE', child_table_name='FACT_ORDERS', foreign_key='employee_code')
        metadata.add_relationship(parent_table_name='FACT_ORDERS', child_table_name='FACT_ORDERS_LINES', foreign_key='order_code')
        metadata.add_relationship(parent_table_name='DIM_PRODUCTS', child_table_name='FACT_ORDERS_LINES', foreign_key='product_code')
        
        return metadata
    except ImportError:
        return None

def generate_dim_products(num_products=120):
    """
    Sinh dữ liệu Bảng Sản phẩm/Hàng hóa (DIM_PRODUCTS) với ít nhất 100 SKU thời trang Local Brand.
    """
    brands_catalog = {
        'Coolmate': [('Áo thun > Basic Tee', 160000, 290000), ('Áo Polo > Smart Casual', 290000, 420000), ('Menswear > Quần Lót Bamboo', 70000, 150000)],
        'Bad Rabbit': [('Áo thun > Graphic Tee', 350000, 480000), ('Pants > Short Nỉ Wave', 380000, 520000), ('Outerwear > Hoodie', 550000, 790000)],
        'DKMV': [('Áo thun > Basic Tee', 150000, 260000), ('Womenswear > Madria Dress', 450000, 650000), ('Outerwear > Varsity Jacket', 520000, 780000)],
        'Teeworld': [('Áo thun > Graphic Tee', 220000, 350000), ('Accessories > Cap', 120000, 220000)],
        'DirtyCoins': [('Áo thun > Graphic Tee Endless', 320000, 450000), ('Pants > Baggy Jeans', 480000, 720000)],
        'Now Saigon': [('Áo thun > Basic Tee', 180000, 320000), ('Áo Polo > Streetwear', 320000, 450000)],
        'The Orbit': [('Unisex > Outfit Bundle Jersey', 450000, 680000), ('Pants > Denim Short', 350000, 520000)],
        'TSUN': [('Áo thun > Graphic Logo Tee', 280000, 420000), ('Outerwear > Jacket', 480000, 750000)],
        'SWE': [('Áo thun > Oversize Tee', 290000, 430000), ('Outerwear > Hoodie Sweater', 500000, 760000)],
        'Teelab': [('Áo thun > Basic Logo', 170000, 290000), ('Pants > Shorts', 220000, 380000)]
    }
    
    sizes = ['S', 'M', 'L', 'XL']
    colors = ['Đen', 'Trắng', 'Xám', 'Be', 'Xanh Navy', 'Rêu', 'Nâu']
    
    products = []
    prod_counter = 1000
    
    brands = list(brands_catalog.keys())
    
    for i in range(num_products):
        prod_counter += 1
        brand = random.choice(brands)
        cat_info = random.choice(brands_catalog[brand])
        cat_path, min_p, max_p = cat_info
        
        uom = 'Bộ' if 'Bundle' in cat_path else ('Chiếc' if 'Cap' in cat_path or 'Short' in cat_path else 'Cái')
        base_sale_price = int(round(random.randint(min_p, max_p), -3))
        base_cost_price = int(round(base_sale_price * random.uniform(0.38, 0.52), -3))
        
        size = random.choice(sizes)
        color = random.choice(colors)
        item_type = cat_path.split(' > ')[-1]
        prod_name = f"{brand} {item_type} {color} - Size {size}"
        
        prod_code = f"SKU-{brand[:3].upper()}-{prod_counter}"
        barcode = f"893{random.randint(100000000, 999999999)}"
        
        products.append({
            'product_code': prod_code,
            'barcode': barcode,
            'product_type': 'Hàng hóa',
            'category_path': cat_path,
            'product_name': prod_name,
            'brand': brand,
            'uom': uom,
            'sale_price': base_sale_price,
            'cost_price': base_cost_price,
            'stock_on_hand': 0, # Will be set by apply_rule_r2_inventory_backfill
            'min_stock': 10,
            'max_stock': 300,
            'weight': random.choice([200, 350, 500, 750, 1000]),
            'conversion_rate': 1,
            'is_active': True,
            'is_direct_sale': True
        })
        
    return pd.DataFrame(products)

def generate_dim_customers(num_customers=350):
    """
    Sinh dữ liệu Khách hàng (DIM_CUSTOMERS) Gen Z / Local Brand.
    """
    cities = ['Hà Nội', 'TP. Hồ Chí Minh', 'Đà Nẵng', 'Hải Phòng', 'Cần Thơ', 'Bình Dương', 'Đồng Nai']
    customer_types = ['Cá nhân', 'Cá nhân', 'Cá nhân', 'Doanh nghiệp']
    
    customers = []
    for i in range(1, num_customers + 1):
        cust_code = f"CUST-{i:04d}"
        cust_name = fake.name()
        c_type = random.choice(customer_types)
        city = random.choice(cities)
        
        customers.append({
            'customer_code': cust_code,
            'customer_name': cust_name,
            'customer_type': c_type,
            'phone': fake.phone_number(),
            'address': fake.street_address(),
            'area': city,
            'ward': f"Phường {random.randint(1, 25)}",
            'company': fake.company() if c_type == 'Doanh nghiệp' else '',
            'tax_code': f"031{random.randint(1000000, 9999999)}" if c_type == 'Doanh nghiệp' else '',
            'dob': fake.date_of_birth(minimum_age=16, maximum_age=32).strftime('%Y-%m-%d'),
            'last_transaction_date': '', # Will be backfilled
            'current_debt': 0.0,
            'total_sales': 0.0, # Will be backfilled
            'status': 1
        })
    return pd.DataFrame(customers)

def generate_dim_employees(num_employees=25):
    """
    Sinh dữ liệu Nhân viên (DIM_EMPLOYEE).
    """
    departments = ['Bán hàng Online', 'Cửa hàng Flagship', 'Kho & Vận chuyển', 'Marketing']
    titles = ['Nhân viên bán hàng', 'Trưởng ca', 'Chuyên viên tư vấn', 'Nhân viên kho']
    branches = ['Chi nhánh Hàng Bông (HN)', 'Chi nhánh Quận 1 (HCM)', 'Kho Tổng Bình Dương']
    
    employees = []
    for i in range(1, num_employees + 1):
        emp_code = f"EMP-{i:03d}"
        employees.append({
            'employee_code': emp_code,
            'employee_name': fake.name(),
            'phone': fake.phone_number(),
            'department': random.choice(departments),
            'title': random.choice(titles),
            'login': f"emp{i:03d}",
            'branch_working': random.choice(branches),
            'salary': float(random.choice([7500000, 9000000, 11000000, 14000000])),
            'dob': fake.date_of_birth(minimum_age=20, maximum_age=40).strftime('%Y-%m-%d'),
            'start_date': fake.date_between(start_date='-3y', end_date='-3m').strftime('%Y-%m-%d')
        })
    return pd.DataFrame(employees)

def generate_fact_invoices_and_lines(df_products, df_customers, df_employees, num_invoices=1500):
    """
    Sinh dữ liệu Hóa đơn (FACT_INVOICES) & Chi tiết (FACT_INVOICES_LINES).
    Tuân thủ Rule R1 (HDIP...) & Timeline constraint (created < shipped < delivered).
    Khớp unit_price với sale_price của DIM_PRODUCTS.
    """
    invoices = []
    invoice_lines = []
    
    product_codes = df_products['product_code'].tolist()
    product_price_map = dict(zip(df_products['product_code'], df_products['sale_price']))
    customer_codes = df_customers['customer_code'].tolist()
    employee_codes = df_employees['employee_code'].tolist()
    
    start_date = datetime.now() - timedelta(days=365)
    line_id_counter = 1
    
    for i in range(1, num_invoices + 1):
        inv_code = format_invoice_code(i)
        cust_code = random.choice(customer_codes)
        emp_code = random.choice(employee_codes)
        
        # Timeline constraint
        created_dt = start_date + timedelta(seconds=random.randint(0, 365 * 86400))
        shipped_dt = created_dt + timedelta(hours=random.randint(2, 24))
        delivered_dt = shipped_dt + timedelta(days=random.randint(1, 4))
        
        num_items = random.choices([1, 2, 3, 4, 5], weights=[0.45, 0.30, 0.15, 0.07, 0.03])[0]
        selected_prod_codes = random.sample(product_codes, num_items)
        
        inv_total_amount = 0.0
        
        for p_code in selected_prod_codes:
            qty = random.choices([1, 2, 3], weights=[0.8, 0.15, 0.05])[0]
            unit_price = float(product_price_map[p_code])
            
            disc_percent = random.choice([0, 0, 0, 5, 10, 15])
            disc_amount = float(round((unit_price * qty) * (disc_percent / 100.0), -3))
            line_total = float((unit_price * qty) - disc_amount)
            inv_total_amount += line_total
            
            invoice_lines.append({
                'invoice_line_id': line_id_counter,
                'invoice_code': inv_code,
                'product_code': p_code,
                'quantity': qty,
                'unit_price': unit_price,
                'line_discount_percent': float(disc_percent),
                'line_discount_amount': disc_amount,
                'line_total': line_total
            })
            line_id_counter += 1
            
        invoices.append({
            'invoice_code': inv_code,
            'customer_code': cust_code,
            'employee_code': emp_code,
            'total_amount': inv_total_amount,
            'order_created_at': created_dt.strftime('%Y-%m-%d %H:%M:%S'),
            'shipped_at': shipped_dt.strftime('%Y-%m-%d %H:%M:%S'),
            'delivered_at': delivered_dt.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    return pd.DataFrame(invoices), pd.DataFrame(invoice_lines)

def generate_fact_orders_and_lines(df_products, df_customers, df_employees, num_orders=500):
    """
    Sinh dữ liệu Đơn đặt hàng (FACT_ORDERS) & Chi tiết (FACT_ORDERS_LINES).
    """
    orders = []
    order_lines = []
    
    product_codes = df_products['product_code'].tolist()
    product_price_map = dict(zip(df_products['product_code'], df_products['sale_price']))
    customer_codes = df_customers['customer_code'].tolist()
    employee_codes = df_employees['employee_code'].tolist()
    
    statuses = ['Hoàn thành', 'Hoàn thành', 'Đang xử lý', 'Đã hủy']
    start_date = datetime.now() - timedelta(days=180)
    line_id_counter = 1
    
    for i in range(1, num_orders + 1):
        ord_code = format_order_code(i)
        cust_code = random.choice(customer_codes)
        emp_code = random.choice(employee_codes)
        order_time = start_date + timedelta(seconds=random.randint(0, 180 * 86400))
        status = random.choice(statuses)
        
        num_items = random.randint(1, 3)
        selected_prod_codes = random.sample(product_codes, num_items)
        
        ord_total_amount = 0.0
        for p_code in selected_prod_codes:
            qty = random.randint(1, 2)
            unit_price = float(product_price_map[p_code])
            disc_amount = 0.0
            line_total = float(unit_price * qty)
            ord_total_amount += line_total
            
            order_lines.append({
                'order_line_id': line_id_counter,
                'order_code': ord_code,
                'product_code': p_code,
                'quantity': qty,
                'unit_price': unit_price,
                'discount_percent': 0.0,
                'discount_amount': disc_amount,
                'line_total': line_total
            })
            line_id_counter += 1
            
        amount_paid = ord_total_amount if status == 'Hoàn thành' else (float(int(ord_total_amount * 0.5)) if status == 'Đang xử lý' else 0.0)
        amount_due = float(ord_total_amount - amount_paid)
        
        orders.append({
            'order_code': ord_code,
            'order_time': order_time.strftime('%Y-%m-%d %H:%M:%S'),
            'customer_code': cust_code,
            'employee_code': emp_code,
            'amount_due': amount_due,
            'amount_paid': amount_paid,
            'status': status
        })
        
    return pd.DataFrame(orders), pd.DataFrame(order_lines)

def generate_all_synthetic_data(num_products=120, num_invoices=1500, num_customers=350, output_dir="data/csv"):
    """
    Hàm tổng hợp sinh dữ liệu giả lập và thực thi đầy đủ các Business Rules.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Master Data Generation
    df_products = generate_dim_products(num_products)
    df_customers = generate_dim_customers(num_customers)
    df_employees = generate_dim_employees(25)
    
    # 2. Fact Data Generation
    df_invoices, df_invoice_lines = generate_fact_invoices_and_lines(df_products, df_customers, df_employees, num_invoices)
    df_orders, df_order_lines = generate_fact_orders_and_lines(df_products, df_customers, df_employees, 500)
    
    # 3. Apply Rule R2 Inventory Back-filling
    df_products = apply_rule_r2_inventory_backfill(df_products, df_invoice_lines, df_order_lines)
    
    # 4. Apply Customer Metrics Back-filling (total_sales & last_transaction_date)
    df_customers = apply_customer_metrics_backfill(df_customers, df_invoices)
    
    # 5. Financial & Mathematical Logic Validation Check
    is_valid = validate_financial_mathematical_logic(df_invoices, df_invoice_lines)
    if is_valid:
        print("✅ Kiểm tra Ràng buộc Toán học & Tài chính: ĐẠT 100%!")
    else:
        print("⚠️ Cảnh báo: Phát hiện sai lệch số liệu tài chính.")

    # 6. Save CSV files
    df_products.to_csv(os.path.join(output_dir, "DIM_PRODUCTS.csv"), index=False, encoding="utf-8-sig")
    df_customers.to_csv(os.path.join(output_dir, "DIM_CUSTOMERS.csv"), index=False, encoding="utf-8-sig")
    df_employees.to_csv(os.path.join(output_dir, "DIM_EMPLOYEE.csv"), index=False, encoding="utf-8-sig")
    df_invoices.to_csv(os.path.join(output_dir, "FACT_INVOICES.csv"), index=False, encoding="utf-8-sig")
    df_invoice_lines.to_csv(os.path.join(output_dir, "FACT_INVOICES_LINES.csv"), index=False, encoding="utf-8-sig")
    df_orders.to_csv(os.path.join(output_dir, "FACT_ORDERS.csv"), index=False, encoding="utf-8-sig")
    df_order_lines.to_csv(os.path.join(output_dir, "FACT_ORDERS_LINES.csv"), index=False, encoding="utf-8-sig")
    
    return {
        "DIM_PRODUCTS": df_products,
        "DIM_CUSTOMERS": df_customers,
        "DIM_EMPLOYEE": df_employees,
        "FACT_INVOICES": df_invoices,
        "FACT_INVOICES_LINES": df_invoice_lines,
        "FACT_ORDERS": df_orders,
        "FACT_ORDERS_LINES": df_order_lines
    }

def main():
    parser = argparse.ArgumentParser(description="SDV & Rule-based Synthetic Data Generator for Local Brand")
    parser.add_argument("--products", type=int, default=120, help="Minimum number of products (SKUs)")
    parser.add_argument("--invoices", type=int, default=1500, help="Minimum number of invoices")
    parser.add_argument("--customers", type=int, default=350, help="Number of customers")
    parser.add_argument("--output-dir", type=str, default="data/csv", help="Output directory for CSV files")
    args = parser.parse_args()

    results = generate_all_synthetic_data(args.products, args.invoices, args.customers, args.output_dir)
    print(f"✅ Đã tạo xong dữ liệu giả lập chuẩn SDV/KiotViet tại thư mục '{args.output_dir}'!")

if __name__ == "__main__":
    main()
