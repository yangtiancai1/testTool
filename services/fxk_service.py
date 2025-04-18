from typing import Optional
from utils.redis_client import RedisClient
from utils.fxk_api_client import FxkApiClient
from config import (
    FXK_API_BASE_URL, FXK_APP_ID, FXK_APP_SECRET,
    FXK_PERMANENT_CODE, TOKEN_CACHE_KEY,
    TOKEN_EXPIRE_TIME, USER_ID_CACHE_KEY
)
import logging
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FxkService:
    def __init__(self):
        self.redis_client = RedisClient()
        self.api_client = FxkApiClient()
    
    def get_corp_access_token(self, force_refresh=False) -> str:
        """获取企业访问令牌，优先从Redis缓存中获取
        
        Args:
            force_refresh: 是否强制刷新令牌，不使用缓存
            
        Returns:
            str: 企业访问令牌
            
        Raises:
            Exception: 当获取令牌失败时抛出异常
        """
        # 如果强制刷新或者缓存中没有令牌，则获取新令牌
        token = None if force_refresh else self.redis_client.get(TOKEN_CACHE_KEY)
        
        if token:
            logger.info("从Redis缓存中获取企业访问令牌")
            return token

        # 获取新令牌前，确保清除旧令牌
        logger.info("正在获取新的企业访问令牌")
        self.redis_client.delete(TOKEN_CACHE_KEY)
        
        # 最多重试3次
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.api_client.get_corp_access_token()
                if response.is_success():
                    token = response.get_data('corpAccessToken')
                    if token:
                        # 将token存入Redis，设置过期时间
                        self.redis_client.set(TOKEN_CACHE_KEY, token, TOKEN_EXPIRE_TIME)
                        logger.info(f"已获取新的企业访问令牌并存入Redis缓存（第{attempt + 1}次尝试）")
                        return token
                    
                logger.warning(f"第{attempt + 1}次尝试：获取令牌失败，响应中没有corpAccessToken")
                
            except Exception as e:
                logger.error(f"第{attempt + 1}次尝试：获取令牌时发生异常: {str(e)}")
            
            if attempt < max_retries - 1:
                logger.info(f"将在3秒后进行第{attempt + 2}次尝试")
                time.sleep(3)
        
        # 如果所有重试都失败了
        raise Exception("无法获取有效的企业访问令牌，请检查配置或网络连接")
    
    def get_user_id_by_mobile(self, mobile: str) -> str:
        """根据手机号获取用户ID，优先从Redis缓存中获取
        
        Args:
            mobile: 手机号
            
        Returns:
            str: 用户ID
            
        Raises:
            Exception: 当获取用户ID失败时抛出异常
        """
        # 构建用户ID缓存键
        user_id_cache_key = f"{USER_ID_CACHE_KEY}:{mobile}"
        
        # 检查Redis中是否存在有效的用户ID
        cached_user_id = self.redis_client.get(user_id_cache_key)
        if cached_user_id:
            logger.info(f"从Redis缓存中获取手机号 {mobile} 的用户ID")
            return cached_user_id
        
        # 如果缓存中没有用户ID，则请求新的用户ID
        token = self.get_corp_access_token()
        response = self.api_client.get_user_id_by_mobile(token, mobile)
        if response.is_success():
            if 'empList' in response.data and len(response.data['empList']) > 0:
                user_id = response.data['empList'][0]['openUserId']
                # 将用户ID存入Redis，设置24小时过期
                self.redis_client.set(user_id_cache_key, user_id, 24 * 60 * 60)
                logger.info(f"已获取手机号 {mobile} 的用户ID并存入Redis缓存")
                return user_id
            else:
                raise Exception(f"未找到手机号为 {mobile} 的用户")
        raise Exception(f"获取用户ID失败: {response.message}") 