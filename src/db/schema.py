def create_tables(conn):
    """
    Tạo các bảng DDL trong SQLite3 dựa trên thiết kế Data Warehouse KiotViet.
    """
    cursor = conn.cursor()
    
    # 1. Bảng Khách hàng
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS DIM_CUSTOMERS (
        customer_code TEXT PRIMARY KEY,
        customer_name TEXT,
        customer_type TEXT,
        phone TEXT,
        address TEXT,
        area TEXT,
        ward TEXT,
        company TEXT,
        tax_code TEXT,
        dob TEXT,
        last_transaction_date TEXT,
        current_debt REAL DEFAULT 0,
        total_sales REAL DEFAULT 0,
        status INTEGER DEFAULT 1
    );
    """)

    # 2. Bảng Nhân viên
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS DIM_EMPLOYEE (
        employee_code TEXT PRIMARY KEY,
        employee_name TEXT,
        phone TEXT,
        department TEXT,
        title TEXT,
        login TEXT,
        branch_working TEXT,
        salary REAL,
        dob TEXT,
        start_date TEXT
    );
    """)

    # 3. Bảng Sản phẩm / Hàng hóa
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS DIM_PRODUCTS (
        product_code TEXT PRIMARY KEY,
        barcode TEXT,
        product_type TEXT,
        category_path TEXT,
        product_name TEXT,
        brand TEXT,
        uom TEXT,
        sale_price REAL,
        cost_price REAL,
        stock_on_hand INTEGER,
        min_stock INTEGER,
        max_stock INTEGER,
        weight INTEGER,
        conversion_rate INTEGER,
        is_active INTEGER,
        is_direct_sale INTEGER
    );
    """)

    # 4. Bảng Hóa đơn Header
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS FACT_INVOICES (
        invoice_code TEXT PRIMARY KEY,
        customer_code TEXT,
        employee_code TEXT,
        total_amount REAL,
        order_created_at TEXT,
        shipped_at TEXT,
        delivered_at TEXT,
        FOREIGN KEY (customer_code) REFERENCES DIM_CUSTOMERS (customer_code),
        FOREIGN KEY (employee_code) REFERENCES DIM_EMPLOYEE (employee_code)
    );
    """)

    # 5. Bảng Chi tiết Hóa đơn
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS FACT_INVOICES_LINES (
        invoice_line_id INTEGER PRIMARY KEY,
        invoice_code TEXT,
        product_code TEXT,
        quantity INTEGER,
        unit_price REAL,
        line_discount_percent REAL,
        line_discount_amount REAL,
        line_total REAL,
        FOREIGN KEY (invoice_code) REFERENCES FACT_INVOICES (invoice_code),
        FOREIGN KEY (product_code) REFERENCES DIM_PRODUCTS (product_code)
    );
    """)

    # 6. Bảng Đơn đặt hàng Header
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS FACT_ORDERS (
        order_code TEXT PRIMARY KEY,
        order_time TEXT,
        customer_code TEXT,
        employee_code TEXT,
        amount_due REAL,
        amount_paid REAL,
        status TEXT,
        FOREIGN KEY (customer_code) REFERENCES DIM_CUSTOMERS (customer_code),
        FOREIGN KEY (employee_code) REFERENCES DIM_EMPLOYEE (employee_code)
    );
    """)

    # 7. Bảng Chi tiết Đơn đặt hàng
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS FACT_ORDERS_LINES (
        order_line_id INTEGER PRIMARY KEY,
        order_code TEXT,
        product_code TEXT,
        quantity INTEGER,
        unit_price REAL,
        discount_percent REAL,
        discount_amount REAL,
        line_total REAL,
        FOREIGN KEY (order_code) REFERENCES FACT_ORDERS (order_code),
        FOREIGN KEY (product_code) REFERENCES DIM_PRODUCTS (product_code)
    );
    """)

    conn.commit()
