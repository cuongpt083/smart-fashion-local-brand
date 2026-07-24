# Smart Fashion Local Brand - Sales Data Analytics & Dashboard

Hệ thống phân tích dữ liệu bán hàng thời trang cho các thương hiệu Local Brand tại Việt Nam, kết hợp giả lập dữ liệu bằng **Synthetic Data Vault (SDV)**, phân tích thuật toán **RFM & Apriori Market Basket**, kết nối **KiotViet REST API**, và giao diện dashboard tương tác bằng **Streamlit**.

---

## 📌 Tính năng chính

1. **Giả lập dữ liệu thời trang (Synthetic Data Vault - SDV)**
   - **Hàng hoá (`DIM_PRODUCTS`)**: Sinh dữ liệu SKU thuộc 10 thương hiệu Local Brand (Coolmate, Bad Rabbit, DirtyCoins, DKMV, Teeworld...), danh mục (Graphic Tee, Hoodie, Varsity, Baggy Jeans...), màu sắc, kích cỡ, giá vốn & giá bán.
   - **Giao dịch (`FACT_INVOICES` & `FACT_INVOICES_LINES`)**: Mã hóa đơn chuẩn định dạng `HDIP...` (Rule R1), mốc thời gian tuần tự (`order_created_at` < `shipped_at` < `delivered_at`).
   - **Xử lý tồn kho (Rule R2)**: Tự động tổng hợp dữ liệu đã bán và tính ngược lại tồn kho `stock_on_hand` trong `DIM_PRODUCTS`.

2. **Phân tích Nâng cao & Thuật toán (RFM & Apriori)**
   - **Phân khúc khách hàng (RFM Analytics)**: Điểm Recency, Frequency, Monetary (1-5), xếp loại khách hàng (*Champions*, *Loyal*, *At Risk*, *New Customers*...).
   - **Market Basket Analysis (Apriori Algorithm)**: Khai phá luật kết hợp (*Support*, *Confidence*, *Lift*) cho các bộ Outfit / Combo mua kèm.

3. **Marketing Automation & Data Ingestion**
   - **Cá nhân hóa chiến dịch CSKH**: Tự động sinh thông điệp gửi tin nhắn (Zalo ZNS / SMS) kèm Voucher theo từng nhóm phân khúc RFM.
   - **KiotViet REST API Client**: OAuth2 Client kết nối tự động lấy Bearer Token và pull dữ liệu `/products`, `/invoices`, `/customers` từ KiotViet.

4. **Dashboard Trực Quan (Streamlit App)**
   - Doanh thu theo thương hiệu Local Brand, tỷ lệ doanh thu danh mục sản phẩm (Plotly Interactive Charts).
   - Tra cứu dữ liệu chi tiết hàng hóa, hóa đơn giao dịch.

---

## 📁 Cấu trúc Repository

```text
smart-fashion-local-brand/
├── setup_environment.ps1    # Script cài đặt môi trường tự động cho Windows 10
├── requirements.txt         # Danh sách thư viện Python (streamlit, sdv, plotly, faker, pandas...)
├── run_pipeline.py          # Script CLI chạy toàn bộ pipeline (Generate CSV -> Upsert SQLite3)
├── app.py                   # Streamlit Dashboard ứng dụng chính
├── README.md                # Tài liệu hướng dẫn sử dụng dự án
├── data/
│   ├── csv/                 # Dữ liệu CSV sinh bởi module SDV
│   └── smart_fashion.db     # Cơ sở dữ liệu SQLite3 sau khi import/upsert
├── docs/
│   ├── Report Local Brand VN.md
│   └── Data structure Analyse.md
└── src/
    ├── sdv/                 # Module 1: SDV Generator & Business Rules (R1, R2)
    │   ├── __init__.py
    │   ├── generator.py     # Core sinh dữ liệu giả lập cho 7 bảng KiotViet
    │   └── constraints.py   # Định nghĩa quy tắc định dạng và back-fill tồn kho
    ├── db/                  # Module 2: SQLite3 Database & Importer
    │   ├── __init__.py
    │   ├── schema.py        # Thiết lập DDL cho 7 bảng Data Warehouse
    │   └── importer.py      # Logic Import / Upsert dữ liệu từ CSV vào DB
    ├── rfm/                 # Module 3: RFM Customer Analytics
    │   ├── __init__.py
    │   └── rfm_analyzer.py  # Thuật toán phân nhóm khách hàng theo chỉ số R, F, M
    ├── mba/                 # Module 4: Market Basket Analysis (Apriori)
    │   ├── __init__.py
    │   └── apriori_engine.py# Thuật toán Apriori tính toán Support, Confidence, Lift
    ├── marketing/           # Module 5: Marketing Automation
    │   ├── __init__.py
    │   └── messaging_service.py # Tự động cá nhân hóa thông điệp CSKH & gửi SMS/ZNS
    └── data_ingestion/      # Module 6: KiotViet REST API Ingestion Client
        ├── __init__.py
        └── kiotviet_client.py   # Client kết nối OAuth2 & pull dữ liệu từ KiotViet API
```

---

## 🛠️ Hướng dẫn Sử dụng

### 🐧 Trên Linux (Ubuntu / Debian / RHEL)

#### 1. Tạo Môi trường ảo Python & Cài đặt Thư viện
Mở Terminal tại thư mục gốc của repository:

```bash
# 1. Tạo môi trường ảo (venv)
python3 -m venv venv

# 2. Kích hoạt môi trường ảo
source venv/bin/activate

# 3. Cài đặt các thư viện phụ thuộc
pip install --upgrade pip
pip install -r requirements.txt
```

#### 2. Chạy Pipeline Sinh Dữ Liệu & Import vào SQLite3
```bash
python3 run_pipeline.py --products 120 --invoices 1500 --customers 350
```

#### 3. Khởi chạy Streamlit Dashboard
```bash
streamlit run app.py
```

---

### 🪟 Trên Windows (Windows 10 / Windows 11)

#### Cách 1: Tự động hóa bằng PowerShell Script (Khuyên dùng)
Mở **PowerShell** tại thư mục dự án và thực thi:

```powershell
.\setup_environment.ps1
```

> **Lưu ý:** Nếu gặp lỗi ExecutionPolicy trong PowerShell, hãy cấp quyền tạm thời bằng lệnh:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
> .\setup_environment.ps1
> ```

Script sẽ tự động:
- Kiểm tra & cài đặt Python 3, NVM for Windows & Node.js LTS (nếu chưa có).
- Tạo môi trường ảo `.venv` và cài đặt đầy đủ các thư viện trong `requirements.txt`.

#### Cách 2: Cài đặt Thủ công trên Windows
Mở **Command Prompt (CMD)** hoặc **PowerShell**:

```powershell
# 1. Tạo môi trường ảo
python -m venv .venv

# 2. Kích hoạt môi trường ảo (PowerShell)
.\.venv\Scripts\Activate.ps1

# Hoặc kích hoạt trên CMD:
# .\.venv\Scripts\activate.bat

# 3. Cài đặt thư viện
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Chạy Pipeline & Mở Dashboard trên Windows
```powershell
# Sinh dữ liệu và nạp vào SQLite3
python run_pipeline.py

# Khởi chạy Dashboard
streamlit run app.py
```
