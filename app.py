import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

from src.rfm.rfm_analyzer import (
    calculate_rfm,
    segment_summary,
    calculate_rfm_kpis,
    get_segment_recommendation,
    SEGMENT_RECOMMENDATIONS
)
from src.mba.apriori_engine import generate_association_rules, get_top_combos
from src.marketing.messaging_service import generate_campaign_messages, send_simulated_sms
from src.data_ingestion.kiotviet_client import KiotVietClient

st.set_page_config(
    page_title="Smart Fashion Local Brand - RFM & Data Analytics Dashboard",
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
st.caption("Hệ thống Phân tích Dữ liệu Bán hàng, Phân khúc RFM Customer Personas, Apriori Market Basket & SDV Generator")

if not os.path.exists(DB_PATH):
    st.warning("⚠️ Chưa tìm thấy cơ sở dữ liệu `data/smart_fashion.db`. Vui lòng chạy pipeline sinh dữ liệu bằng lệnh:")
    st.code("python run_pipeline.py", language="bash")
    st.stop()

# 1. Base Summary Metrics
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

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Phân Tích Doanh Thu & Brand",
    "🎯 Phân Khúc Khách Hàng (RFM Analytics)",
    "🛒 Combo & Outfit (Apriori MBA)",
    "💬 Marketing Automation",
    "👥 Danh Sách Khách Hàng",
    "📦 Danh Mục Sản Phẩm",
    "🔗 KiotViet Data Ingestion"
])

# TAB 1: BRAND & REVENUE ANALYTICS
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

# TAB 2: ENHANCED RFM CUSTOMER SEGMENTATION DASHBOARD
with tab2:
    st.subheader("🎯 Phân Tích Chân Dung Khách Hàng Thuật Toán RFM (Recency, Frequency, Monetary)")
    st.markdown("""
    Mô hình RFM giúp phân loại tệp khách hàng Gen Z thành **8 phân khúc Chân dung Khách hàng** chuyên biệt, từ đó thiết lập chiến lược giữ chân khách hàng (Retention) và tối ưu giá trị vòng đời (CLV).
    """)
    
    rfm_df = calculate_rfm(df_invoices, df_customers)
    
    if not rfm_df.empty:
        # RFM KPIs
        kpis = calculate_rfm_kpis(rfm_df)
        
        kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)
        with kpi_col1:
            st.metric("Khách Hàng Phân Tích", f"{kpis['total_customers']:,}")
        with kpi_col2:
            st.metric("Tỷ Lệ Khách VIP", f"{kpis['vip_percentage']}% ({kpis['vip_count']} người)")
        with kpi_col3:
            st.metric("Đóng Góp DT Từ VIP", f"{kpis['vip_revenue_share']}%")
        with kpi_col4:
            st.metric("CLV Trung Bình", f"{kpis['avg_clv']:,.0f} ₫")
        with kpi_col5:
            st.metric("Tần Suất Mua TB", f"{kpis['avg_frequency']} đơn/khách")
            
        st.markdown("---")
        
        summary_df = segment_summary(rfm_df)
        
        # Row 1 Charts: Treemap & Donut Chart
        c_chart1, c_chart2 = st.columns(2)
        
        with c_chart1:
            st.write("#### 🌳 Biểu Đồ Treemap: Quy Mô Doanh Thu & Số Khách Hàng theo Phân Khúc")
            fig_tree = px.treemap(
                summary_df,
                path=['segment'],
                values='total_monetary',
                color='customer_count',
                color_continuous_scale='Viridis',
                hover_data=['customer_share_%', 'revenue_share_%', 'avg_monetary'],
                title='Quy Mô Doanh Thu & Khách Hàng (Click để xem chi tiết)'
            )
            st.plotly_chart(fig_tree, use_container_width=True)
            
        with c_chart2:
            st.write("#### 🍩 Biểu Đồ Tỷ Lệ Phân Bộ Chân Dung Khách Hàng")
            fig_donut = px.pie(
                summary_df,
                values='customer_count',
                names='segment',
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Pastel,
                title='Tỷ Lệ Số Lượng Khách Hàng theo 8 Phân Khúc RFM'
            )
            fig_donut.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_donut, use_container_width=True)
            
        # Row 2 Chart: Interactive Scatter Plot (Recency vs Monetary vs Frequency)
        st.markdown("---")
        st.write("#### 🌌 Ma Trận Tọa Độ RFM: Recency (Số Ngày Mua Cuối) vs Monetary (Chi Tiêu) vs Frequency (Tần Suất)")
        fig_scatter = px.scatter(
            rfm_df,
            x='recency',
            y='monetary',
            size='frequency',
            color='segment',
            hover_name='customer_name',
            hover_data=['phone', 'area', 'rfm_score', 'frequency'],
            labels={'recency': 'Số Ngày Kể Từ Lần Mua Cuối (Ngày)', 'monetary': 'Tổng Chi Tiêu Tích Lũy (VND)', 'frequency': 'Tần Suất (Đơn)'},
            title='Phân Bổ Khách Hàng Theo Tọa Độ RFM (Size = Tần Suất Mua Đơn)',
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Row 3: Drill-down & Strategic Recommendations
        st.markdown("---")
        st.subheader("🔍 Tra Cứu Chân Dung & Đề Xuất Hành Động Chiến Lược CSKH")
        
        all_segments = list(SEGMENT_RECOMMENDATIONS.keys())
        selected_seg = st.selectbox("Chọn Phân Khúc Khách Hàng Cần Tra Cứu & Đề Xuất:", options=all_segments)
        
        rec_info = get_segment_recommendation(selected_seg)
        
        st.info(f"**📌 Mô tả Phân khúc `{selected_seg}`**: {rec_info['description']}")
        st.success(f"**🚀 Đề xuất Khuyến nghị Chiến lược CSKH**: {rec_info['action']}")
        
        # Filter customer table for selected segment
        seg_customers = rfm_df[rfm_df['segment'] == selected_seg].copy()
        st.write(f"**Danh sách {len(seg_customers)} khách hàng thuộc nhóm `{selected_seg}`:**")
        
        st.dataframe(
            seg_customers[['customer_code', 'customer_name', 'phone', 'area', 'recency', 'frequency', 'monetary', 'r_score', 'f_score', 'm_score', 'rfm_score']],
            use_container_width=True
        )

# TAB 3: MARKET BASKET ANALYSIS
with tab3:
    st.subheader("🛒 Market Basket Analysis & Gợi Ý Combo Mua Kèm (Apriori Algorithm)")
    df_rules = generate_association_rules(df_lines, df_products, min_support=0.005, min_confidence=0.05)
    if not df_rules.empty:
        top_combos = get_top_combos(df_rules, 15)
        st.write("#### Các Luật Kết Hợp Sản Phẩm Bán Chạy Nhất (Highest Lift & Confidence)")
        st.dataframe(top_combos[['antecedent', 'consequent', 'support', 'confidence', 'lift', 'pair_count']], use_container_width=True)
    else:
        st.info("Chưa có đủ dữ liệu giao dịch trùng lặp để hình thành luật kết hợp Apriori.")

# TAB 4: MARKETING AUTOMATION
with tab4:
    st.subheader("💬 Tự Động Hóa Chiến Dịch Marketing & CSKH")
    rfm_df = calculate_rfm(df_invoices, df_customers)
    if not rfm_df.empty:
        segments = rfm_df['segment'].unique().tolist()
        selected_seg_mkt = st.selectbox("Chọn Phân khúc Khách hàng Mục tiêu cho Chiến dịch:", options=segments)
        voucher_input = st.text_input("Mã Voucher Khuyến Mãi:", value="SUMMERVIBE2024")
        
        msg_df = generate_campaign_messages(rfm_df, target_segment=selected_seg_mkt, voucher_code=voucher_input)
        st.dataframe(msg_df[['customer_code', 'customer_name', 'phone', 'channel', 'message_content', 'status']], use_container_width=True)
        
        if st.button("🚀 Giả lập Gửi Tin Nhắn Hàng Loạt"):
            count = send_simulated_sms(msg_df)
            st.success(f"✅ Đã gửi thành công {count} tin nhắn Zalo ZNS / SMS cho phân khúc '{selected_seg_mkt}'!")

# TAB 5: CUSTOMER MANAGEMENT
with tab5:
    st.subheader("👥 Quản Lý Khách Hàng (DIM_CUSTOMERS - Đã Cập Nhật Theo Real Invoices)")
    if df_customers is not None:
        st.dataframe(
            df_customers[['customer_code', 'customer_name', 'customer_type', 'phone', 'area', 'dob', 'last_transaction_date', 'total_sales', 'status']],
            use_container_width=True
        )

# TAB 6: PRODUCT CATALOG
with tab6:
    st.subheader("📦 Bảng Quản Lý Hàng Hóa & Tồn Kho (DIM_PRODUCTS - Rule R2 Back-filled)")
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

# TAB 7: KIOTVIET INGESTION
with tab7:
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
