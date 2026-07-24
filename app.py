import streamlit as st
import pandas as pd
import os

st.set_page_config(
    page_title="Smart Fashion Local Brand Dashboard",
    page_icon="👕",
    layout="wide"
)

st.title("👕 Smart Fashion Local Brand - Analytics Dashboard")
st.subheader("Phân tích dữ liệu bán hàng & Giả lập Dữ liệu với SDV")

# Check if data exists
products_path = "data/products.csv"
customers_path = "data/customers.csv"

if os.path.exists(products_path) and os.path.exists(customers_path):
    df_products = pd.read_csv(products_path)
    df_customers = pd.read_csv(customers_path)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Tổng SKU Sản phẩm", len(df_products))
    with col2:
        st.metric("Tổng số Khách hàng", len(df_customers))
    with col3:
        st.metric("Giá bán TB (VND)", f"{df_products['selling_price'].mean():,.0f}")
    with col4:
        st.metric("Tổng Tồn kho", f"{df_products['stock_quantity'].sum():,.0f}")
        
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["📦 Danh mục Hàng hoá", "👥 Khách hàng"])
    
    with tab1:
        st.write("### Danh sách Sản phẩm / SKU")
        st.dataframe(df_products, use_container_width=True)
        
    with tab2:
        st.write("### Danh sách Khách hàng")
        st.dataframe(df_customers, use_container_width=True)
else:
    st.info("💡 Chưa tìm thấy dữ liệu. Hãy chạy script `python src/data_generator.py` để sinh dữ liệu mẫu!")
