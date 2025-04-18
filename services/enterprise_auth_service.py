import requests
import time

class EnterpriseAuthService:
    """企业级认证服务"""
    
    def __init__(self, app_id: str, app_secret: str, redirect_uri: str):
        """初始化企业级认证服务
        
        Args:
            app_id: 应用ID
            app_secret: 应用密钥
            redirect_uri: 重定向URI
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.redirect_uri = redirect_uri
        self._access_token_cache = None
        self._access_token_expires_at = 0
        self._user_id_cache = {}  # 添加用户ID缓存字典
        
    def get_corp_access_token(self) -> str:
        """获取企业级访问令牌
        
        Returns:
            str: 企业级访问令牌
        """
        # 检查缓存是否有效
        if self._access_token_cache and time.time() < self._access_token_expires_at:
            return self._access_token_cache
            
        # 获取新的访问令牌
        url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal"
        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()
        
        if response_data.get("code") != 0:
            raise Exception(f"获取企业级访问令牌失败: {response_data.get('msg')}")
            
        # 更新缓存
        self._access_token_cache = response_data["app_access_token"]
        self._access_token_expires_at = time.time() + response_data["expire"] - 300  # 提前5分钟过期
        
        return self._access_token_cache
        
    def get_user_id_by_mobile(self, mobile: str) -> str:
        """通过手机号获取用户ID
        
        Args:
            mobile: 手机号
            
        Returns:
            str: 用户ID
        """
        # 检查缓存是否有效
        if mobile in self._user_id_cache:
            cached_data = self._user_id_cache[mobile]
            if time.time() < cached_data["expires_at"]:
                return cached_data["user_id"]
                
        # 获取新的用户ID
        url = "https://open.feishu.cn/open-apis/contact/v3/users/batch_get_id"
        headers = {
            "Authorization": f"Bearer {self.get_corp_access_token()}",
            "Content-Type": "application/json; charset=utf-8"
        }
        data = {
            "mobiles": [mobile]
        }
        
        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()
        
        if response_data.get("code") != 0:
            raise Exception(f"获取用户ID失败: {response_data.get('msg')}")
            
        if not response_data["data"]["user_list"]:
            raise Exception(f"未找到手机号 {mobile} 对应的用户")
            
        user_id = response_data["data"]["user_list"][0]["user_id"]
        
        # 更新缓存，设置24小时过期
        self._user_id_cache[mobile] = {
            "user_id": user_id,
            "expires_at": time.time() + 24 * 60 * 60
        }
        
        return user_id 