from typing import Dict, Any, List, Optional
from utils.fxk_api_client import FxkApiClient
from services.fxk_service import FxkService
from services.interfaces import ICustomObjectService
import logging
from utils.redis_client import RedisClient
from config import USER_ID_CACHE_KEY

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CustomObjectService(ICustomObjectService):
    """自定义对象服务类，用于查询和管理自定义对象"""
    
    def __init__(self, fxk_service: FxkService, api_client: FxkApiClient):
        """初始化自定义对象服务
        
        Args:
            fxk_service: FxkService实例
            api_client: FxkApiClient实例
        """
        self.fxk_service = fxk_service
        self.api_client = api_client
        self.corp_access_token = None
        self.user_id_cache = {}  # 添加用户ID缓存
    
    def set_corp_access_token(self, token: str):
        """设置企业访问令牌
        
        Args:
            token: 企业访问令牌
        """
        self.corp_access_token = token
        logger.info("已设置企业访问令牌")
    
    def query_custom_objects(self,
                           data_object_api_name: str,
                           mobile: str,
                           limit: int = 100,
                           offset: int = 0,
                           filters: Optional[List[Dict[str, Any]]] = None,
                           orders: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """查询自定义对象数据
        
        Args:
            data_object_api_name: 对象API名称
            mobile: 用户手机号
            limit: 每页记录数
            offset: 偏移量
            filters: 过滤条件列表
            orders: 排序条件列表
            
        Returns:
            Dict[str, Any]: 查询结果
        """
        # 最多重试3次
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 获取企业访问令牌，如果是重试则强制刷新
                corp_access_token = self.fxk_service.get_corp_access_token(force_refresh=(attempt > 0))
                
                # 获取用户ID
                user_id = self.fxk_service.get_user_id_by_mobile(mobile)
                
                # 获取企业ID
                corp_id = self.api_client.get_corp_id()
                
                # 构建查询条件
                search_query_info = {
                    "limit": limit,
                    "offset": offset
                }
                
                # 添加过滤条件
                if filters:
                    search_query_info["filters"] = filters
                    
                # 添加排序条件
                if orders:
                    search_query_info["orders"] = orders
                    
                # 记录请求参数
                logger.info(f"查询对象 {data_object_api_name} 的请求参数:")
                logger.info(f"- 企业访问令牌: {corp_access_token[:10]}...")
                logger.info(f"- 当前用户ID: {user_id}")
                logger.info(f"- 企业ID: {corp_id}")
                logger.info(f"- 查询条件: {search_query_info}")
                
                # 发送请求
                response = self.api_client.query_custom_object(
                    corp_access_token=corp_access_token,
                    current_open_user_id=user_id,
                    data_object_api_name=data_object_api_name,
                    search_query_info=search_query_info,
                    corp_id=corp_id
                )
                
                # 记录响应结果
                logger.info(f"查询对象 {data_object_api_name} 的 API 响应:")
                logger.info(f"- 响应状态: {'成功' if response.is_success() else '失败'}")
                if not response.is_success():
                    logger.info(f"- 响应码: {response.code}")
                    logger.info(f"- 响应消息: {response.message}")
                    logger.info(f"- 响应数据: {response.data}")
                    
                    # 如果是令牌过期错误，继续重试
                    if response.code == 20016:
                        if attempt < max_retries - 1:
                            logger.warning(f"令牌已过期，正在进行第 {attempt + 1} 次重试")
                            continue
                        else:
                            logger.error(f"获取对象 {data_object_api_name} 数据时发生错误: TOKEN_EXPIRED")
                            return {"dataList": [], "total": 0}
                            
                return response.data
                
            except Exception as e:
                logger.error(f"第{attempt + 1}次尝试：获取对象 {data_object_api_name} 数据时发生异常: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"将在3秒后进行第{attempt + 2}次尝试")
                    import time
                    time.sleep(3)
                else:
                    logger.error(f"获取对象 {data_object_api_name} 数据失败，已达到最大重试次数")
                    return {"dataList": [], "total": 0}
        
        return {"dataList": [], "total": 0}
    
    def get_custom_object_by_id(self, 
                               data_object_api_name: str, 
                               mobile: str,
                               object_id: str) -> Dict[str, Any]:
        """根据ID获取自定义对象详情
        
        Args:
            data_object_api_name: 对象的api_name，例如：DeliveryNoteProductObj
            mobile: 当前用户的手机号，用于获取用户ID
            object_id: 自定义对象ID
            
        Returns:
            Dict[str, Any]: 包含自定义对象详情的响应
            
        Raises:
            Exception: 当API调用失败时抛出异常
        """
        # 参数验证
        if not data_object_api_name:
            raise ValueError("data_object_api_name不能为空")
        if not mobile:
            raise ValueError("mobile不能为空")
        if not object_id:
            raise ValueError("object_id不能为空")
            
        # 构建查询条件，精确匹配ID
        filters = [
            {
                "field_name": "id",
                "field_values": [object_id],
                "operator": "EQ"
            }
        ]
        
        # 查询自定义对象
        response_data = self.query_custom_objects(
            data_object_api_name=data_object_api_name,
            mobile=mobile,
            limit=1,
            offset=0,
            filters=filters
        )
        
        # 检查是否找到对象
        if 'data' in response_data and 'dataList' in response_data['data']:
            data_list = response_data['data']['dataList']
            if data_list and len(data_list) > 0:
                return data_list[0]
                
        # 如果未找到对象，返回空字典
        return {} 