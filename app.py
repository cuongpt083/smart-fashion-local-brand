import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os

from src.rfm.rfm_analyzer import calculate_rfm, segment_summary
from src.mba.apriori_engine import generate_association_rules, get_top_combos
from src.marketing.messaging_service import generate_campaign_messages, send_simulated_sms
from src.data_ingestion.kiotviet_client import KiotVietClient

st.set_page_config(
    page_title="Smart Fashion Local Brand Dashboard",
    page_icon="👕",
    layout="wide"
)

DB_PATH = "data/smart_fashion.db"

@st.cache_data(ttl=60)
def load_data_from_db(query):
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

st.title("👕 Smart Fashion Local Brand - Analytics Dashboard")
st.caption("Hệ thống Phân tích Dữ liệu Bán hàng, Phân khúc RFM, Apriori Market Basket & SDV Generator")

if not os.path.exists(DB_PATH):
    st.warning("⚠️ Chưa tìm thấy cơ sở dữ liệu `data/smart_fashion.db`. Vui lòng chạy pipeline sinh dữ liệu bằng lệnh:")
    st.code("python run_pipeline.py", language="bash")
    st.stop()

# 1. Summary Metrics
df_invoices = load_data_from_db("SELECT * FROM FACT_INVOICES")
df_products = load_data_from_db("SELECT * FROM DIM_PRODUCTS")
df_customers = load_data_from_db("SELECT * FROM DIM_CUSTOMERS")
df_lines = load_data_from_db("SELECT * FROM FACT_INVOICES_LINES")

total_revenue = df_invoices['total_amount'].sum() if df_invoices is not None else 0
total_invoices = len(df_invoices) if df_invoices is not None else 0
total_skus = len(df_products) if df_products is not None else 0
total_custs = len(df_customers) if df_customers is not None else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Tổng Doanh Thu (VND)", f"{total_revenue:,.0f} ₫")
with col2:
    st.metric("Tổng Số Hóa Đơn", f"{total_invoices:,}")
with col3:
    st.metric("Tổng Số SKU (Hàng hóa)", f"{total_skus:,}")
with col4:
    st.metric("Tổng Số Khách Hàng", f"{total_custs:,}")

st.markdown("---")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Phân Tích Doanh Thu & Brand",
    "🎯 Phân Khúc Khách Hàng (RFM)",
    "🛒 Combo & Outfit (Apriori MBA)",
    "💬 Marketing Automation",
    "🔗 KiotViet Data Ingestion",
    "📦 Danh Mục Sản Phẩm"
])

with tab1:
    st.subheader("Doanh thu theo Thương hiệu Local Brand & Danh mục")
    df_brand_rev = load_data_from_db("""
        SELECT p.brand, SUM(l.line_total) as brand_revenue, SUM(l.quantity) as total_qty
        FROM FACT_INVOICES_LINES l
        JOIN DIM_PRODUCTS p ON l.product_code = p.product_code
        GROUP BY p.brand
        ORDER BY brand_revenue DESC
    """)
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        if df_brand_rev is not None and not df_brand_rev.empty:
            fig_brand = px.bar(
                df_brand_rev,
                x='brand',
                y='brand_revenue',
                color='brand',
                title='Top Doanh Thu theo Nhãn Hàng Local Brand',
                labels={'brand_revenue': 'Doanh thu (VND)', 'brand': 'Thương hiệu'}
            )
            st.plotly_chart(fig_brand, use_container_width=True)
    with col_chart2:
        df_cat_rev = load_data_from_db("""
            SELECT p.category_path, SUM(l.line_total) as cat_revenue
            FROM FACT_INVOICES_LINES l
            JOIN DIM_PRODUCTS p ON l.product_code = p.product_code
            GROUP BY p.category_path
            ORDER BY cat_revenue DESC
        """)
        if df_cat_rev is not None and not df_cat_rev.empty:
            fig_cat = px.pie(
                df_cat_rev,
                values='cat_revenue',
                names='category_path',
                title='Tỷ Lệ Doanh Thu theo Phân Loại Sản Phẩm',
                hole=0.4
            )
            st.plotly_chart(fig_cat, use_container_width=True)

with tab2:
    st.subheader("🎯 Phân Khúc Khách Hàng RFM (Recency, Frequency, Monetary)")
    rfm_df = calculate_rfm(df_invoices, df_customers)
    if not rfm_df.empty:
        summary_df = segment_summary(rfm_df)
        c1, c2 = st.columns([1, 2])
        with c1:
            st.dataframe(summary_df, use_container_width=True)
        with c2:
            fig_rfm = px.pie(
                summary_df,
                values='customer_count',
                names='segment',
                title='Tỷ Lệ Phân Khúc Khách Hàng Gen Z',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig_rfm, use_container_width=True)
            
        st.subheader("Bảng Chi Tiết Điểm RFM Khách Hàng")
        st.dataframe(rfm_df, use_container_width=True)

with tab3:
    st.subheader("🛒 Market Basket Analysis & Gợi Ý Combo Mua Kèm (Apriori Algorithm)")
    df_rules = generate_association_rules(df_lines, df_products, min_support=0.005, min_confidence=0.05)
    if not df_rules.empty:
        top_combos = get_top_combos(df_rules, 15)
        st.write("#### Các Luật Kết Hợp Sản Phẩm Bán Chạy Nhất (Highest Lift & Confidence)")
        st.dataframe(top_combos[['antecedent', 'consequent', 'support', 'confidence', 'lift', 'pair_count']], use_container_width=True)
    else:
        st.info("Chưa có đủ dữ liệu giao dịch trùng lặp để hình thành luật kết hợp Apriori.")

with tab4:
    st.subheader("💬 Tự Động Hóa Chiến Dịch Marketing & CSKH")
    rfm_df = calculate_rfm(df_invoices, df_customers)
    if not rfm_df.empty:
        segments = rfm_df['segment'].unique().tolist()
        selected_seg = st.selectbox("Chọn Phân khúc Khách hàng Mục tiêu:", options=segments)
        voucher_input = st.text_input("Mã Voucher Khuyến Mãi:", value="SUMMERVIBE2024")
        
        msg_df = generate_campaign_messages(rfm_df, target_segment=selected_seg, voucher_code=voucher_input)
        st.dataframe(msg_df[['customer_code', 'customer_name', 'phone', 'channel', 'message_content', 'status']], use_container_width=True)
        
        if st.button("🚀 Giả lập Gửi Tin Nhắn Hàng Loạt"):
            count = send_simulated_sms(msg_df)
            st.success(f"✅ Đã gửi thành công {count} tin nhắn Zalo ZNS / SMS cho phân khúc '{selected_seg}'!")

with tab5:
    st.subheader("🔗 KiotViet Data Ingestion REST API Client")
    st.info("Module kết nối trực tiếp với tài khoản KiotViet thực tế thông qua OAuth2 REST API Client.")
    
    col_k1, col_k2, col_k3 = st.columns(3)
    with col_k1:
        client_id = st.text_input("Client ID:", value=os.getenv("KIOTVIET_CLIENT_ID", ""))
    with col_k2:
        client_secret = st.text_input("Client Secret:", type="password", value=os.getenv("KIOTVIET_CLIENT_SECRET", ""))
    with col_k3:
        retailer = st.text_input("Retailer Name:", value=os.getenv("KIOTVIET_RETAILER", ""))
        
    if st.button("🔌 Kiểm Tra Kết Nối REST API KiotViet"):
        client = KiotVietClient(client_id=client_id, client_secret=client_secret, retailer=retailer)
        if client.authenticate():
            st.success("✅ Kết nối KiotViet API thành công!")
        else:
            st.warning("⚠️ Không thể kết nối. Vui lòng kiểm tra lại thông tin Client ID & Secret.")

with tab6:
    st.subheader("📦 Bảng Quản Lý Hàng Hóa & Tồn Kho (DIM_PRODUCTS)")
    if df_products is not None:
        brand_filter = st.multiselect("Lọc theo Thương hiệu:", options=df_products['brand'].unique().tolist())
        if brand_filter:
            filtered_df = df_products[df_products['brand'].isin(brand_filter)]
        else:
            filtered_df = df_products
            
        st.dataframe(
            filtered_df[['product_code', 'product_name', 'brand', 'category_path', 'sale_price', 'cost_price', 'stock_on_hand', 'uom']],
            use_container_width=True
        )
