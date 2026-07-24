import requests
import json
import os
from typing import Dict, Any, Optional

class KiotVietClient:
    """
    Client kết nối và tự động pull dữ liệu từ KiotViet REST API.
    Sử dụng phương thức xác thực OAuth2 (Client Credentials Flow).
    """
    AUTH_URL = "https://id.kiotviet.vn/connect/token"
    BASE_API_URL = "https://public.kiotapi.com"
    
    def __init__(self, client_id: str = "", client_secret: str = "", retailer: str = ""):
        self.client_id = client_id or os.getenv("KIOTVIET_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("KIOTVIET_CLIENT_SECRET", "")
        self.retailer = retailer or os.getenv("KIOTVIET_RETAILER", "")
        self.access_token: Optional[str] = None
        
    def authenticate(self) -> bool:
        """
        Lấy OAuth2 Bearer Token từ KiotViet Identity Service.
        """
        if not self.client_id or not self.client_secret or not self.retailer:
            print("⚠️ Thiếu thông tin xác thực KiotViet (client_id, client_secret, retailer). Khoảng trống kết nối API.")
            return False
            
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials',
            'scopes': 'PublicApi.Access'
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        try:
            res = requests.post(self.AUTH_URL, data=payload, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                self.access_token = data.get("access_token")
                print("✅ Tự động xác thực OAuth2 KiotViet thành công!")
                return True
            else:
                print(f"❌ Xác thực KiotViet thất bại: {res.status_code} - {res.text}")
                return False
        except Exception as e:
            print(f"❌ Lỗi kết nối KiotViet Auth Server: {e}")
            return False
            
    def _get_headers(self) -> Dict[str, str]:
        return {
            'Authorization': f"Bearer {self.access_token}",
            'Retailer': self.retailer,
            'Content-Type': 'application/json'
        }
        
    def fetch_products(self, pageSize: int = 100) -> Dict[str, Any]:
        """Pull danh sách sản phẩm từ REST API `/products`."""
        if not self.access_token and not self.authenticate():
            return {"data": []}
            
        url = f"{self.BASE_API_URL}/products?pageSize={pageSize}"
        try:
            res = requests.get(url, headers=self._get_headers(), timeout=15)
            return res.json() if res.status_code == 200 else {"error": res.text}
        except Exception as e:
            return {"error": str(e)}

    def fetch_invoices(self, pageSize: int = 100) -> Dict[str, Any]:
        """Pull danh sách hóa đơn từ REST API `/invoices`."""
        if not self.access_token and not self.authenticate():
            return {"data": []}
            
        url = f"{self.BASE_API_URL}/invoices?pageSize={pageSize}"
        try:
            res = requests.get(url, headers=self._get_headers(), timeout=15)
            return res.json() if res.status_code == 200 else {"error": res.text}
        except Exception as e:
            return {"error": str(e)}

    def fetch_customers(self, pageSize: int = 100) -> Dict[str, Any]:
        """Pull danh sách khách hàng từ REST API `/customers`."""
        if not self.access_token and not self.authenticate():
            return {"data": []}
            
        url = f"{self.BASE_API_URL}/customers?pageSize={pageSize}"
        try:
            res = requests.get(url, headers=self._get_headers(), timeout=15)
            return res.json() if res.status_code == 200 else {"error": res.text}
        except Exception as e:
            return {"error": str(e)}
