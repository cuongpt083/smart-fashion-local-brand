import pandas as pd
import numpy as np
from datetime import datetime

SEGMENT_RECOMMENDATIONS = {
    'Champions (VIP)': {
        'description': 'Khách hàng VIP nhất, mua thường xuyên với giá trị đơn hàng rất lớn.',
        'action': '⭐ Gửi thư cảm ơn từ Founder, trao quyền xem trước & mua trước các Bộ Sưu Tập (BST) phiên bản giới hạn, quà tặng độc quyền nhân ngày sinh nhật.',
        'color': '#2ecc71'
    },
    'Loyal Customers': {
        'description': 'Khách hàng thân thiết mua sắm định kỳ và có phản hồi rất tốt.',
        'action': '🎁 Tặng điểm thưởng nhân đôi, mã giảm giá 15% cho các đơn hàng tiếp theo, rủ tham gia chương trình khách hàng thân thiết.',
        'color': '#3498db'
    },
    'Potential Loyalists': {
        'description': 'Khách hàng mới mua 2-3 đơn gần đây với giá trị tốt, có tiềm năng thành VIP.',
        'action': '👕 Đề xuất các combo outfit phối sẵn (Curated Outfits), gửi mã Voucher Upsell gia tăng giá trị đơn hàng tiếp theo.',
        'color': '#9b59b6'
    },
    'New Customers': {
        'description': 'Khách hàng mới chốt đơn đầu tiên gần đây.',
        'action': '👋 Gửi tin nhắn chào mừng (Onboarding SMS/Zalo), hướng dẫn bảo quản trang phục và tặng Voucher 10% cho lần mua thứ 2.',
        'color': '#1abc9c'
    },
    'At Risk (Cần Giữ Chân)': {
        'description': 'Khách hàng từng mua nhiều đơn giá trị cao nhưng đã lâu không quay lại.',
        'action': '🚨 Gửi chiến dịch Re-engagement: Tặng Voucher Winback 20% - 25% + FreeShip, gửi catalogue các mẫu Hot Trend mới nhất.',
        'color': '#e67e22'
    },
    'Cannot Lose Them': {
        'description': 'Khách hàng VIP cũ có nguy cơ cao rời bỏ thương hiệu.',
        'action': '📞 Gọi điện CSKH trực tiếp, lắng nghe góp ý về dịch vụ/chất lượng sản phẩm và tặng ưu đãi đặc biệt cá nhân hóa.',
        'color': '#e74c3c'
    },
    'About to Sleep': {
        'description': 'Khách hàng sắp rời bỏ, tần suất mua ít và giá trị đơn trung bình.',
        'action': '📢 Nhắc nhở tích điểm sắp hết hạn, giới thiệu các chương trình Flash Sale hoặc xả kho giảm giá sâu.',
        'color': '#f39c12'
    },
    'Lost Customers': {
        'description': 'Khách hàng đã lâu không tương tác và có tần suất/giá trị mua thấp.',
        'action': '💤 Đưa vào danh sách theo dõi chiến dịch Remarketing chi phí thấp hoặc chạy quảng cáo bám đuổi (Retargeting Ads).',
        'color': '#95a5a6'
    }
}

def calculate_rfm(df_invoices: pd.DataFrame, df_customers: pd.DataFrame = None, reference_date=None) -> pd.DataFrame:
    """
    Tính toán chỉ số RFM (Recency, Frequency, Monetary) và phân loại 8 phân khúc Chân dung Khách hàng
    từ cơ sở dữ liệu SQLite3 (FACT_INVOICES & DIM_CUSTOMERS).
    """
    if df_invoices is None or df_invoices.empty:
        return pd.DataFrame()
        
    df_inv = df_invoices.copy()
    df_inv['order_created_at'] = pd.to_datetime(df_inv['order_created_at'])
    
    if reference_date is None:
        reference_date = df_inv['order_created_at'].max() + pd.Timedelta(days=1)
    else:
        reference_date = pd.to_datetime(reference_date)
        
    # Aggregate metrics per customer
    rfm = df_inv.groupby('customer_code').agg({
        'order_created_at': lambda x: int((reference_date - x.max()).days),
        'invoice_code': 'nunique',
        'total_amount': 'sum'
    }).reset_index()
    
    rfm.columns = ['customer_code', 'recency', 'frequency', 'monetary']
    rfm['monetary'] = rfm['monetary'].round(0)
    
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
        rfm = rfm.merge(
            df_customers[['customer_code', 'customer_name', 'phone', 'area', 'customer_type', 'dob']],
            on='customer_code',
            how='left'
        )
        
    return rfm

# Alias for backward compatibility
segment_customers = calculate_rfm

def classify_rfm_segment(row) -> str:
    r, f, m = row['r_score'], row['f_score'], row['m_score']
    
    if r >= 4 and f >= 4 and m >= 4:
        return 'Champions (VIP)'
    elif r >= 3 and f >= 3 and m >= 3:
        return 'Loyal Customers'
    elif r >= 4 and f >= 2 and m >= 2:
        return 'Potential Loyalists'
    elif r >= 4 and f == 1:
        return 'New Customers'
    elif r <= 2 and f >= 4 and m >= 4:
        return 'Cannot Lose Them'
    elif r <= 2 and f >= 3 and m >= 3:
        return 'At Risk (Cần Giữ Chân)'
    elif r <= 3 and f <= 2 and m <= 2:
        return 'About to Sleep'
    else:
        return 'Lost Customers'

def calculate_rfm_kpis(rfm_df: pd.DataFrame) -> dict:
    if rfm_df is None or rfm_df.empty:
        return {}
        
    total_cust = len(rfm_df)
    vips = len(rfm_df[rfm_df['segment'] == 'Champions (VIP)'])
    vip_pct = (vips / total_cust * 100) if total_cust > 0 else 0.0
    
    total_rev = rfm_df['monetary'].sum()
    vip_rev = rfm_df[rfm_df['segment'] == 'Champions (VIP)']['monetary'].sum()
    vip_rev_pct = (vip_rev / total_rev * 100) if total_rev > 0 else 0.0
    
    avg_clv = rfm_df['monetary'].mean()
    avg_freq = rfm_df['frequency'].mean()
    avg_recency = rfm_df['recency'].mean()
    
    return {
        'total_customers': total_cust,
        'vip_count': vips,
        'vip_percentage': round(vip_pct, 1),
        'vip_revenue_share': round(vip_rev_pct, 1),
        'avg_clv': round(avg_clv, 0),
        'avg_frequency': round(avg_freq, 2),
        'avg_recency': round(avg_recency, 1)
    }

def segment_summary(rfm_df: pd.DataFrame) -> pd.DataFrame:
    if rfm_df is None or rfm_df.empty:
        return pd.DataFrame()
        
    total_rev = rfm_df['monetary'].sum()
    total_cust = len(rfm_df)
    
    summary = rfm_df.groupby('segment').agg(
        customer_count=('customer_code', 'count'),
        avg_recency=('recency', 'mean'),
        avg_frequency=('frequency', 'mean'),
        total_monetary=('monetary', 'sum'),
        avg_monetary=('monetary', 'mean')
    ).reset_index()
    
    summary['customer_share_%'] = (summary['customer_count'] / total_cust * 100).round(1)
    summary['revenue_share_%'] = (summary['total_monetary'] / total_rev * 100).round(1) if total_rev > 0 else 0.0
    
    summary = summary.sort_values(by='total_monetary', ascending=False)
    return summary

def get_segment_recommendation(segment_name: str) -> dict:
    return SEGMENT_RECOMMENDATIONS.get(segment_name, {
        'description': 'Phân khúc khách hàng chung.',
        'action': 'Triển khai các chương trình khuyến mãi thông thường.',
        'color': '#7f8c8d'
    })
