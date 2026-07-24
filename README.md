# Smart Fashion Local Brand - Sales Data Analytics & Dashboard

Hệ thống phân tích dữ liệu bán hàng thời trang cho các thương hiệu Local Brand tại Việt Nam, kết hợp giả lập dữ liệu bằng **Synthetic Data Vault (SDV)** và giao diện dashboard tương tác bằng **Streamlit**.

---

## 📌 Tính năng chính

1. **Giả lập dữ liệu thời trang (Synthetic Data Generation with SDV)**
   - **Hàng hoá (Products & SKUs)**: Mã sản phẩm, Bộ sưu tập (BST), Danh mục (T-shirt, Hoodie, Pants, Accessories), Size (S/M/L/XL), Màu sắc, Giá vốn & Giá niêm yết.
   - **Khách hàng (Customers)**: Thông tin khách hàng, hạng thành viên (Loyalty level), Tỉnh/Thành phố.
   - **Giao dịch (Orders & Invoices)**: Đơn hàng đa kênh (Online/Store), Chi tiết sản phẩm, Trạng thái đơn, Phương thức thanh toán, Thời gian giao dịch.

2. **Dashboard Phân Tích (Streamlit App)**
   - Tổng quan doanh thu, lợi nhuận, AOV (Average Order Value).
   - Phân tích hiệu quả các Bộ Sưu Tập & Sản phẩm bán chạy (Top Sellers & Stock Aging).
   - Phân khúc khách hàng (RFM Analysis) và tỷ lệ quay lại.
   - Báo cáo chi tiết theo kênh bán hàng và khoảng thời gian.

---

## 🛠️ Hướng dẫn cài đặt (Windows 10)

### 1. Tự động thiết lập môi trường bằng PowerShell
Mở **PowerShell** tại thư mục dự án và chạy:

```powershell
.\setup_environment.ps1
```

> **Lưu ý:** Nếu gặp lỗi ExecutionPolicy trong PowerShell, bạn có thể cấp quyền tạm thời bằng lệnh:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
> .\setup_environment.ps1
> ```

Script sẽ tự động:
- Kiểm tra & Cài đặt **Python 3** (nếu chưa có).
- Kiểm tra & Cài đặt **NVM for Windows** và Node.js LTS.
- Tạo Python Virtual Environment (`.venv`).
- Cài đặt đầy đủ các thư viện trong `requirements.txt` (`streamlit`, `sdv`, `pandas`, `plotly`, ...).

---

## 🚀 Khởi chạy ứng dụng

1. Kích hoạt môi trường ảo:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

2. Chạy Dashboard Streamlit:
   ```bash
   streamlit run app.py
   ```

---

## 📁 Cấu trúc dự án dự kiến

```text
smart-fashion-local-brand/
├── setup_environment.ps1    # Script cài đặt tự động cho Windows 10
├── requirements.txt         # Thư viện Python cần thiết (SDV, Streamlit, Pandas...)
├── README.md                # Tài liệu hướng dẫn
├── data/                    # Thư mục chứa dữ liệu sinh bởi SDV (.csv / .parquet)
├── src/
│   ├── data_generator.py    # Script sinh dữ liệu giả lập sử dụng SDV & Faker
│   └── utils.py             # Xử lý dữ liệu và tính toán chỉ số KPI
└── app.py                   # Giao diện chính ứng dụng Streamlit Dashboard
```
