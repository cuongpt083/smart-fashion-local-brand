Dựa trên các tài liệu hướng dẫn thực hành và tài liệu nghiên cứu thị trường Local Brand, để xây dựng một Data Warehouse (Kho dữ liệu) và thiết lập kịch bản sinh dữ liệu giả lập (SDV script) mô phỏng chính xác hệ thống KiotViet, chúng ta cần thiết kế chi tiết danh sách các bảng (Table), các cột (Column), kiểu dữ liệu (Datatype) và đặc biệt là các ràng buộc nghiệp vụ (Business Rules).  
Dưới đây là mô tả chi tiết:

### 1\. Danh sách thiết kế Table, Column và Datatype

Hệ thống được chia thành 2 nhóm chính: **Master Data (Dimension Tables)** và **Transactional Data (Fact Tables)**.

#### A. Nhóm Bảng Danh Mục (Master Data \- Dimension)

Đây là các bảng tồn tại độc lập, không phụ thuộc vào giao dịch bán hàng, đóng vai trò làm dữ liệu tham chiếu (seed data) 1, 2\.  
**1\. Bảng Khách hàng (DIM\_CUSTOMERS)** 1, 3

* customer\_code (Primary Key): Mã khách hàng \- *Varchar*.  
* customer\_name, customer\_type, phone, address, area, ward, company, tax\_code: Các thuộc tính mô tả \- *Varchar*.  
* dob (Ngày sinh), last\_transaction\_date (Ngày giao dịch cuối): *Date-time*.  
* current\_debt (Nợ cần thu hiện tại), total\_sales (Tổng bán): *Numeric*.  
* status (Trạng thái kích hoạt): *Integer* (1 \= Kích hoạt, 0 \= Không kích hoạt).

**2\. Bảng Nhân viên (DIM\_EMPLOYEE)** 4, 5

* employee\_code (Primary Key): Mã nhân viên \- *Varchar*.  
* employee\_name, phone, department, title, login, branch\_working: Thuộc tính định danh và công việc \- *Varchar*.  
* salary (Mức lương): *Numeric*.  
* dob (Ngày sinh), start\_date (Ngày bắt đầu làm việc): *Date-time*.

**3\. Bảng Sản phẩm/Hàng hóa (DIM\_PRODUCTS)** 2, 6, 7

* product\_code (Primary Key): Mã hàng hóa/SKU \- *Varchar*.  
* barcode: Mã vạch (Unique, có thể Null một phần) \- *Varchar*.  
* product\_type, category\_path, product\_name, brand, uom (Đơn vị tính): *Varchar*.  
* sale\_price (Giá bán), cost\_price (Giá vốn): *Numeric*.  
* stock\_on\_hand (Tồn kho), min\_stock (Tồn nhỏ nhất), max\_stock (Tồn lớn nhất), weight (Trọng lượng), conversion\_rate (Quy đổi): *Integer*.  
* is\_active (Đang kinh doanh), is\_direct\_sale (Được bán trực tiếp): *Boolean*.

#### B. Nhóm Bảng Giao Dịch (Transactional Data \- Fact)

Dữ liệu phát sinh từ hoạt động bán hàng, được tách thành bảng chung (Header) và bảng chi tiết (Lines) để tránh dư thừa dữ liệu 8, 9\.  
**4\. Bảng Hóa đơn (FACT\_INVOICES)** 9-11

* invoice\_code (Primary Key): Mã hóa đơn \- *Varchar* (Bắt buộc có tiền tố HDIP).  
* total\_amount (Tổng tiền): *Numeric*.  
* order\_created\_at, shipped\_at, delivered\_at: Các mốc thời gian \- *Date-time*.

**5\. Bảng Chi tiết Hóa đơn (FACT\_INVOICES\_LINES)** 10

* invoice\_line\_id (Primary Key): ID dòng chi tiết.  
* invoice\_code (Foreign Key): Tham chiếu tới FACT\_INVOICES.  
* product\_code (Foreign Key): Tham chiếu tới DIM\_PRODUCTS.  
* quantity (Số lượng), unit\_price (Đơn giá), line\_discount\_percent, line\_discount\_amount, line\_total (Thành tiền): *Numeric* hoặc *Integer* (đối với số lượng).

**6\. Bảng Đơn đặt hàng (FACT\_ORDERS) & Chi tiết (FACT\_ORDERS\_LINES)** 12, 13

* Lưu trữ các giao dịch tạm giữ chỗ, chưa thanh toán với cấu trúc tương tự hóa đơn.  
* Bao gồm: order\_code (PK), order\_time (*Date-time*), customer\_code, amount\_due, amount\_paid (*Numeric*), status (*Varchar*) cho bảng cha 12\.  
* Và order\_line\_id (PK), order\_code (FK), product\_code (FK), quantity, unit\_price, discount\_percent, discount\_amount, line\_total cho bảng con 13\.

### 2\. Các Business Rules thiết lập trong script SDV (Synthetic Data Vault)

CTGAN (mô hình AI của SDV) là mô hình xác suất, nếu không có sự can thiệp sẽ sinh ra các điểm dữ liệu vô lý như "ngày giao hàng trước ngày đặt hàng" hoặc "hóa đơn có tổng tiền âm" 14\. Để dữ liệu giả lập có độ tương thích 100% với KiotViet, SDV script cần thiết lập các hàm ràng buộc nghiệp vụ (Constraints) sau:  
**A. Ràng buộc Logic Toán học & Tài chính (Mathematical Logic)**

* **SDV ColumnFormula Constraint:** Tổng tiền hóa đơn (final\_price hoặc total\_amount) không được sinh ngẫu nhiên. Nó bắt buộc phải tuân theo công thức kế toán: Bằng tổng đơn giá nhân số lượng (line\_total \== qty \* price), cộng phí ship, trừ đi các voucher trợ giá 11, 15\. Tổng của hóa đơn phải khớp với SUM(line\_total) của các dòng chi tiết 11\.  
* **SDV Positive / Tùy chỉnh:** Số lượng mua (quantity) bắt buộc phải \> 0; Đơn giá (unit\_price) và Giảm giá (discount) phải \>= 0 16, 17\.  
* **Tính nhất quán dữ liệu (Data Consistency):** Cột Đơn giá (unit\_price) trong bảng FACT bắt buộc phải khớp (bằng) với Giá bán (sale\_price) của chính sản phẩm đó trong bảng DIM\_PRODUCTS tại cùng thời điểm 11, 12\.

**B. Ràng buộc Quy luật Dòng chảy Thời gian (Timeline Validity)**

* **SDV Inequality / ChainedInequality Constraint:** Hệ thống phải đảm bảo tính tuần tự của chuỗi cung ứng. Cụ thể: order\_created\_at (Lúc tạo đơn) \< shipped\_at (Giao cho vận chuyển) \< delivered\_at (Khách nhận thành công) 18\.  
* **Giá khuyến mãi:** Giá bán ra đợt Sale (discounted\_price) luôn phải nhỏ hơn giá gốc (original\_price) 18\.

**C. Ràng buộc Toàn vẹn Tham chiếu (Referential Integrity)**

* **Khóa ngoại (Foreign Key Validation):** Bất kỳ mã product\_code, customer\_code, employee\_code nào xuất hiện trong các bảng FACT (FACT\_INVOICES, FACT\_ORDERS) đều phải có mặt trong các bảng DIM tương ứng, không được để null hoặc trỏ vào dữ liệu ma 11, 17\.  
* **SDV CarryOverColumns Constraint:** Đảm bảo các thuộc tính trạng thái được kế thừa chính xác từ bảng Parent sang bảng Child. Ví dụ, chiết khấu hạng thành viên "Gold" ở bảng Khách hàng phải được chuyển sang đúng hóa đơn của người đó ở bảng Hóa đơn, không được lấy nhầm chiết khấu của "Silver" 19, 20\.

**D. Ràng buộc Quy chuẩn Phân loại Hàng hóa & Độc bản**

* **SDV FixedCombinations Constraint:** Ngăn chặn việc hoán vị ngẫu nhiên sai logic của hệ thống. Ví dụ: Đảm bảo danh mục chính "Đồ lót nam" không bao giờ đi kèm nhóm phụ là "Váy hoa nhí" hay thương hiệu Coolmate bị gán cho đồ nữ 21, 22\.  
* **SDV OneHotEncoding:** Khống chế các biến phân mảnh như Kích cỡ chỉ được nằm trong các không gian tĩnh (S, M, L, XL), không sinh ra kích cỡ trung gian 21\.  
* **Quy định tiền tố (Rule R1):** Mã hóa đơn (invoice\_code) bắt buộc tuân thủ định dạng Regex có tiền tố là HDIP kèm theo các số tăng dần 13, 23\.  
* **SDV UniqueCombinations & Range Constraint:** Mã voucher cho user phải là duy nhất. Độ tuổi khách hàng (nếu có) bị khống chế từ 12-27 tuổi; Rating sản phẩm từ 1-5 sao 16\.

**E. Ràng buộc Xử lý Tồn kho (Rule R2 \- Inventory Logic)**

* Hệ thống yêu cầu số lượng bán (quantity) phải luôn nhỏ hơn hoặc bằng số tồn kho (stock\_on\_hand) 23\.  
* Trong SDV pipeline, thay vì ép AI tính toán cộng dồn trực tiếp (vì rất nặng), script áp dụng chiến lược **Iterative Back-filling (Post-processing)**: Cho phép sinh hóa đơn bình thường, sau đó dùng thuật toán hậu xử lý cộng tổng số lượng đã bán của từng mặt hàng, và cập nhật ngược lại cột stock\_on\_hand trong DIM\_PRODUCTS sao cho Tồn kho \>= Tổng đã bán \+ Số lượng dự trữ 23-25.

