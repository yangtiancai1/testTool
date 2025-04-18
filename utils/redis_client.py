import redis
from config import REDIS_HOST, REDIS_PORT, REDIS_DB

class RedisClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
            cls._instance.client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=True
            )
        return cls._instance
    
    def get(self, key):
        return self.client.get(key)
    
    def set(self, key, value, expire_time=None):
        self.client.set(key, value, ex=expire_time)
    
    def delete(self, key):
        self.client.delete(key)
    
    def exists(self, key):
        return self.client.exists(key)
    
    def keys(self, pattern: str) -> list:
        """获取匹配模式的键列表"""
        return self.client.keys(pattern) 