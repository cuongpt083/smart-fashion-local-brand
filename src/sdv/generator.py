import os
import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta
from .constraints import format_invoice_code, format_order_code, apply_rule_r2_inventory_backfill

fake = Faker('vi_VN')

def generate_dim_products(num_products=120):
    brands = ['Coolmate', 'Bad Rabbit', 'DKMV', 'Teeworld', 'DirtyCoins', 'Now Saigon', 'The Orbit', 'TSUN', 'SWE', 'Teelab']
    
    categories = {
        'Áo thun > Graphic Tee': (180000, 420000, 'Cái'),
        'Áo thun > Basic Tee': (150000, 320000, 'Cái'),
        'Áo Polo > Smart Casual': (280000, 520000, 'Cái'),
        'Outerwear > Hoodie': (450000, 750000, 'Cái'),
        'Outerwear > Varsity Jacket': (550000, 950000, 'Cái'),
        'Pants > Baggy Jeans': (380000, 650000, 'Cái'),
        'Pants > Short Nỉ': (220000, 450000, 'Cái'),
        'Accessories > Cap & Socks': (50000, 180000, 'Chiếc')
    }
    
    sizes = ['S', 'M', 'L', 'XL']
    colors = ['Đen', 'Trắng', 'Xám', 'Be', 'Xanh Navy', 'Rêu', 'Nâu']
    
    products = []
    prod_counter = 1000
    
    for _ in range(num_products):
        prod_counter += 1
        brand = random.choice(brands)
        cat_path = random.choice(list(categories.keys()))
        min_p, max_p, uom = categories[cat_path]
        
        base_sale_price = int(round(random.randint(min_p, max_p), -3))
        base_cost_price = int(round(base_sale_price * random.uniform(0.35, 0.52), -3))
        
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
            'stock_on_hand': 0,
            'min_stock': 10,
            'max_stock': 300,
            'weight': random.choice([200, 350, 500, 750, 1000]),
            'conversion_rate': 1,
            'is_active': True,
            'is_direct_sale': True
        })
        
    return pd.DataFrame(products)

def generate_dim_customers(num_customers=350):
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
            'last_transaction_date': '',
            'current_debt': 0,
            'total_sales': 0,
            'status': 1
        })
    return pd.DataFrame(customers)

def generate_dim_employees(num_employees=25):
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
            'salary': random.choice([7500000, 9000000, 11000000, 14000000]),
            'dob': fake.date_of_birth(minimum_age=20, maximum_age=40).strftime('%Y-%m-%d'),
            'start_date': fake.date_between(start_date='-3y', end_date='-3m').strftime('%Y-%m-%d')
        })
    return pd.DataFrame(employees)

def generate_fact_invoices_and_lines(df_products, df_customers, df_employees, num_invoices=1500):
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
        
        created_dt = start_date + timedelta(seconds=random.randint(0, 365 * 86400))
        shipped_dt = created_dt + timedelta(hours=random.randint(2, 24))
        delivered_dt = shipped_dt + timedelta(days=random.randint(1, 4))
        
        num_items = random.choices([1, 2, 3, 4, 5], weights=[0.45, 0.30, 0.15, 0.07, 0.03])[0]
        selected_prod_codes = random.sample(product_codes, num_items)
        
        inv_total_amount = 0
        
        for p_code in selected_prod_codes:
            qty = random.choices([1, 2, 3], weights=[0.8, 0.15, 0.05])[0]
            unit_price = product_price_map[p_code]
            
            disc_percent = random.choice([0, 0, 0, 5, 10, 15])
            disc_amount = int(round(unit_price * qty * (disc_percent / 100.0), -3))
            line_total = (unit_price * qty) - disc_amount
            inv_total_amount += line_total
            
            invoice_lines.append({
                'invoice_line_id': line_id_counter,
                'invoice_code': inv_code,
                'product_code': p_code,
                'quantity': qty,
                'unit_price': unit_price,
                'line_discount_percent': disc_percent,
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
        
        ord_total_amount = 0
        for p_code in selected_prod_codes:
            qty = random.randint(1, 2)
            unit_price = product_price_map[p_code]
            disc_amount = 0
            line_total = unit_price * qty
            ord_total_amount += line_total
            
            order_lines.append({
                'order_line_id': line_id_counter,
                'order_code': ord_code,
                'product_code': p_code,
                'quantity': qty,
                'unit_price': unit_price,
                'discount_percent': 0,
                'discount_amount': disc_amount,
                'line_total': line_total
            })
            line_id_counter += 1
            
        amount_paid = ord_total_amount if status == 'Hoàn thành' else (int(ord_total_amount * 0.5) if status == 'Đang xử lý' else 0)
        amount_due = ord_total_amount - amount_paid
        
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
    os.makedirs(output_dir, exist_ok=True)
    
    df_products = generate_dim_products(num_products)
    df_customers = generate_dim_customers(num_customers)
    df_employees = generate_dim_employees(25)
    
    df_invoices, df_invoice_lines = generate_fact_invoices_and_lines(df_products, df_customers, df_employees, num_invoices)
    df_orders, df_order_lines = generate_fact_orders_and_lines(df_products, df_customers, df_employees, 500)
    
    df_products = apply_rule_r2_inventory_backfill(df_products, df_invoice_lines, df_order_lines)
    
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
