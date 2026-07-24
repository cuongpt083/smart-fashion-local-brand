import pandas as pd
import numpy as np
from datetime import datetime

def calculate_rfm(df_invoices, df_customers=None, reference_date=None):
    """
    Tính toán các chỉ số RFM (Recency, Frequency, Monetary) từ bảng FACT_INVOICES.
    - Recency (R): Số ngày kể từ lần mua gần nhất đến reference_date.
    - Frequency (F): Tổng số đơn hàng mua thành công.
    - Monetary (M): Tổng giá trị chi tiêu (VND).
    """
    if df_invoices is None or df_invoices.empty:
        return pd.DataFrame()
        
    df_inv = df_invoices.copy()
    df_inv['order_created_at'] = pd.to_datetime(df_inv['order_created_at'])
    
    if reference_date is None:
        reference_date = df_inv['order_created_at'].max() + pd.Timedelta(days=1)
    else:
        reference_date = pd.to_datetime(reference_date)
        
    rfm = df_inv.groupby('customer_code').agg({
        'order_created_at': lambda x: (reference_date - x.max()).days,
        'invoice_code': 'count',
        'total_amount': 'sum'
    }).reset_index()
    
    rfm.columns = ['customer_code', 'recency', 'frequency', 'monetary']
    
    # Calculate R, F, M Score (1 - 5) using quantiles
    try:
        rfm['r_score'] = pd.qcut(rfm['recency'], 5, labels=[5, 4, 3, 2, 1], duplicates='drop')
    except Exception:
        rfm['r_score'] = 3
        
    try:
        rfm['f_score'] = pd.qcut(rfm['frequency'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5], duplicates='drop')
    except Exception:
        rfm['f_score'] = 3
        
    try:
        rfm['m_score'] = pd.qcut(rfm['monetary'], 5, labels=[1, 2, 3, 4, 5], duplicates='drop')
    except Exception:
        rfm['m_score'] = 3

    rfm['r_score'] = rfm['r_score'].astype(int)
    rfm['f_score'] = rfm['f_score'].astype(int)
    rfm['m_score'] = rfm['m_score'].astype(int)
    
    rfm['rfm_score'] = rfm['r_score'].astype(str) + rfm['f_score'].astype(str) + rfm['m_score'].astype(str)
    
    # Classify Customer Segments
    rfm['segment'] = rfm.apply(classify_rfm_segment, axis=1)
    
    if df_customers is not None and not df_customers.empty:
        rfm = rfm.merge(df_customers[['customer_code', 'customer_name', 'phone', 'area']], on='customer_code', how='left')
        
    return rfm

def classify_rfm_segment(row):
    r, f, m = row['r_score'], row['f_score'], row['m_score']
    
    if r >= 4 and f >= 4 and m >= 4:
        return 'Champions (VIP)'
    elif r >= 3 and f >= 3 and m >= 3:
        return 'Loyal Customers'
    elif r >= 4 and f <= 2:
        return 'New Customers'
    elif r >= 3 and f >= 2 and m >= 2:
        return 'Potential Loyalists'
    elif r <= 2 and f >= 3 and m >= 3:
        return 'At Risk (Cần Giữ Chân)'
    elif r <= 2 and f <= 2:
        return 'Lost Customers'
    else:
        return 'About to Sleep'

def segment_summary(rfm_df):
    if rfm_df.empty:
        return pd.DataFrame()
    return rfm_df.groupby('segment').agg(
        customer_count=('customer_code', 'count'),
        avg_recency=('recency', 'mean'),
        avg_frequency=('frequency', 'mean'),
        total_monetary=('monetary', 'sum')
    ).reset_index().sort_values(by='customer_count', ascending=False)
