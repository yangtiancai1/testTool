def get_user_id_by_mobile(self, mobile: str) -> str:
        """根据手机号获取用户ID
        
        Args:
            mobile: 用户手机号
            
        Returns:
            str: 用户ID
        """
        # 检查Redis中是否有用户ID缓存
        redis_client = RedisClient()
        user_id_cache_key = f"{USER_ID_CACHE_KEY}:{mobile}"
        cached_user_id = redis_client.get(user_id_cache_key)
        
        if cached_user_id:
            logger.info(f"从Redis缓存中获取手机号 {mobile} 的用户ID")
            return cached_user_id
            
        # 获取企业访问令牌
        corp_access_token = self.get_corp_access_token()
        
        # 获取企业ID
        corp_id = self.api_client.get_corp_id()
        
        # 获取用户ID
        response = self.api_client.get_user_id_by_mobile(
            corp_access_token=corp_access_token,
            mobile=mobile,
            corp_id=corp_id
        )
        
        if response.is_success() and response.data and 'empList' in response.data:
            user_id = response.data['empList'][0]['openUserId']
            # 缓存用户ID
            redis_client.set(user_id_cache_key, user_id)
            return user_id
        else:
            raise ValueError(f"获取用户ID失败: {response.message}") 