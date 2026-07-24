import pandas as pd

TEMPLATES = {
    'Champions (VIP)': "🔥 [LOCAL BRAND] Chào {customer_name}! Cảm ơn bạn đã luôn đồng hành cùng shop. Tặng bạn Mã Voucher VIP {voucher_code} giảm 20% cho BST mới nhất!",
    'Loyal Customers': "✨ [LOCAL BRAND] Cảm ơn {customer_name} đã yêu thích sản phẩm của shop. Nhận ngay Voucher {voucher_code} giảm 15% cho đơn hàng tiếp theo nhé!",
    'At Risk (Cần Giữ Chân)': "🎁 [LOCAL BRAND] Đã lâu chưa thấy {customer_name} ghé shop! Shop gửi bạn Voucher đặc biệt {voucher_code} giảm 25% + FreeShip cho đơn từ 300k. Đừng bỏ lỡ!",
    'New Customers': "🥳 [LOCAL BRAND] Chào mừng {customer_name} đến với gia đình Local Brand! Tặng bạn Voucher {voucher_code} giảm 10k cho đơn hàng thứ 2.",
    'Default': "👕 [LOCAL BRAND] Chào {customer_name}! Nhập mã {voucher_code} để nhận ưu đãi 10% tuần này!"
}

def generate_campaign_messages(rfm_df, target_segment='At Risk (Cần Giữ Chân)', voucher_code='LOCALBRAND2024'):
    """
    Sinh danh sách tin nhắn CSKH/Marketing cá nhân hóa dựa trên phân khúc RFM.
    """
    if rfm_df is None or rfm_df.empty:
        return pd.DataFrame()
        
    filtered = rfm_df[rfm_df['segment'] == target_segment].copy()
    if filtered.empty:
        filtered = rfm_df.head(20).copy()
        
    template = TEMPLATES.get(target_segment, TEMPLATES['Default'])
    
    messages = []
    for idx, row in filtered.iterrows():
        c_name = row.get('customer_name', 'Khách hàng')
        c_phone = row.get('phone', 'N/A')
        msg = template.format(customer_name=c_name, voucher_code=voucher_code)
        
        messages.append({
            'customer_code': row['customer_code'],
            'customer_name': c_name,
            'phone': c_phone,
            'segment': target_segment,
            'channel': 'Zalo ZNS / SMS',
            'message_content': msg,
            'status': 'Ready to Send'
        })
        
    return pd.DataFrame(messages)

def send_simulated_sms(messages_df):
    """
    Mô phỏng gửi tin nhắn marketing.
    """
    if messages_df is None or messages_df.empty:
        return 0
    messages_df['status'] = 'Sent Successfully'
    return len(messages_df)
