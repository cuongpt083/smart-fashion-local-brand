import os
import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta

# Initialize Faker with Vietnamese locale
fake = Faker('vi_VN')

def generate_fashion_products(num_products=50):
    """
    Sinh dữ liệu giả lập cho danh mục Hàng hoá (Products / SKUs) local brand thời trang.
    """
    categories = {
        'T-Shirt': (250000, 450000),
        'Hoodie & Sweater': (450000, 750000),
        'Jacket & Coat': (600000, 1200000),
        'Pants & Short': (350000, 600000),
        'Accessories': (100000, 300000)
    }
    
    collections = ['Summer Vibe 2024', 'Streetwear Classic', 'Urban Cyberpunk', 'Minimalist Essential', 'Autumn Breeze']
    sizes = ['S', 'M', 'L', 'XL']
    colors = ['Đen', 'Trắng', 'Xám', 'Be', 'Xanh Navy', 'Rêu']
    
    products = []
    product_id = 1000
    
    for _ in range(num_products):
        cat = random.choice(list(categories.keys()))
        col = random.choice(collections)
        min_p, max_p = categories[cat]
        base_price = round(random.randint(min_p, max_p), -4)
        cost_price = int(base_price * random.uniform(0.35, 0.5))
        
        prod_name = f"{cat} {fake.word().capitalize()} {random.choice(colors)}"
        
        for size in sizes:
            product_id += 1
            products.append({
                'product_id': f"SKU-{product_id}",
                'product_name': prod_name,
                'category': cat,
                'collection': col,
                'size': size,
                'color': random.choice(colors),
                'cost_price': cost_price,
                'selling_price': base_price,
                'stock_quantity': random.randint(10, 150)
            })
            
    return pd.DataFrame(products)

def generate_customers(num_customers=200):
    """
    Sinh dữ liệu giả lập về Khách hàng.
    """
    cities = ['Hà Nội', 'TP. Hồ Chí Minh', 'Đà Nẵng', 'Hải Phòng', 'Cần Thơ', 'Bình Dương', 'Đồng Nai']
    tiers = ['Standard', 'Silver', 'Gold', 'VIP']
    
    customers = []
    for i in range(1, num_customers + 1):
        customers.append({
            'customer_id': f"CUST-{i:04d}",
            'customer_name': fake.name(),
            'phone_number': fake.phone_number(),
            'city': random.choice(cities),
            'tier': random.choices(tiers, weights=[0.6, 0.25, 0.1, 0.05])[0],
            'registered_date': fake.date_between(start_date='-2y', end_date='today')
        })
    return pd.DataFrame(customers)

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    df_products = generate_fashion_products(30)
    df_customers = generate_customers(100)
    
    df_products.to_csv("data/products.csv", index=False, encoding="utf-8-sig")
    df_customers.to_csv("data/customers.csv", index=False, encoding="utf-8-sig")
    
    print("✅ Đã tạo dữ liệu mẫu thành công tại thư mục 'data/'!")
