import os
import json
import logging
import threading
from logging.handlers import RotatingFileHandler
from typing import Dict, Any, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from services.interfaces import ICustomObjectService
from services.custom_object_service import CustomObjectService
from services.fxk_service import FxkService
from services.enterprise_auth_service import EnterpriseAuthService
from utils.fxk_api_client import FxkApiClient
from utils.redis_client import RedisClient
from config import TOKEN_CACHE_KEY

# 配置日志
# 创建日志目录
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 生成带时间戳的日志文件名
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = os.path.join(log_dir, f"custom_object_data_{timestamp}.log")

# 创建日志格式
formatter = logging.Formatter('%(asctime)s - [线程 %(thread)d] - %(levelname)s - %(message)s')

# 创建文件处理器，限制单个文件大小为10MB，最多保留5个备份文件
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# 配置根日志记录器
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.info(f"日志文件已创建: {log_file}")

class CustomObjectDataService:
    """自定义对象数据服务"""
    
    def __init__(self, mobile: str, custom_object_service: Optional[ICustomObjectService] = None):
        """初始化自定义对象数据服务
        
        Args:
            mobile: 用户手机号
            custom_object_service: 自定义对象服务实例，可选
        """
        self.mobile = mobile
        
        # 创建或使用提供的自定义对象服务
        if custom_object_service is None:
            # 创建依赖服务
            fxk_service = FxkService()
            api_client = FxkApiClient()
            self.custom_object_service = CustomObjectService(fxk_service=fxk_service, api_client=api_client)
            
            # 检查Redis中是否有企业访问令牌缓存
            redis_client = RedisClient()
            cached_token = redis_client.get(TOKEN_CACHE_KEY)
            if cached_token:
                logger.info("从Redis缓存中获取企业访问令牌")
                self.custom_object_service.set_corp_access_token(cached_token)
            else:
                # 预先获取企业访问令牌
                corp_access_token = fxk_service.get_corp_access_token()
                logger.info("已预先获取企业访问令牌")
                self.custom_object_service.set_corp_access_token(corp_access_token)
        else:
            self.custom_object_service = custom_object_service
            
    def fetch_object_data(self, 
                         object_api_name: str, 
                         filters: Optional[List[Dict[str, Any]]] = None,
                         orders: Optional[List[Dict[str, Any]]] = None,
                         limit: int = 100,
                         custom_object_service: Optional[ICustomObjectService] = None) -> Dict[str, Any]:
        """获取指定对象的数据
        
        Args:
            object_api_name: 对象API名称
            filters: 过滤条件列表
            orders: 排序条件列表
            limit: 每页记录数
            custom_object_service: 自定义对象服务实例，可选
            
        Returns:
            Dict[str, Any]: 对象数据
        """
        # 使用传入的服务实例或默认实例
        service = custom_object_service or self.custom_object_service
        
        all_data = []
        offset = 0
        total = 0
        max_retries = 2  # 最大重试次数
        retry_count = 0
        
        while True:
            try:
                # 获取对象数据
                logger.info(f"获取对象 {object_api_name} 的第 {offset//limit + 1} 页数据")
                response_data = service.query_custom_objects(
                    data_object_api_name=object_api_name,
                    mobile=self.mobile,
                    limit=limit,
                    offset=offset,
                    filters=filters,
                    orders=orders
                )
                
                # 检查是否是令牌过期错误
                if "errorCode" in response_data and response_data["errorCode"] == "20016":
                    if retry_count < max_retries:
                        retry_count += 1
                        logger.warning(f"令牌已过期，正在进行第 {retry_count} 次重试")
                        # 清除Redis中的令牌缓存
                        redis_client = RedisClient()
                        redis_client.delete(TOKEN_CACHE_KEY)
                        # 重新获取令牌并重试
                        continue
                    else:
                        logger.error(f"令牌过期重试次数已达上限 ({max_retries})")
                        break
                
                # 确保返回正确的数据结构
                if "data" in response_data:
                    data = response_data["data"]
                    data_list = data.get("dataList", [])
                    current_total = data.get("total", 0)
                    
                    # 如果是第一次查询，设置总记录数
                    if offset == 0:
                        total = current_total
                        logger.info(f"对象 {object_api_name} 共有 {total} 条记录")
                    
                    # 添加当前页的数据
                    all_data.extend(data_list)
                    logger.info(f"对象 {object_api_name} 当前已获取 {len(all_data)}/{total} 条记录")
                    
                    # 如果已经获取了所有数据或没有更多数据，退出循环
                    if len(all_data) >= total or len(data_list) == 0:
                        break
                        
                    # 更新偏移量
                    offset += limit
                else:
                    logger.warning(f"对象 {object_api_name} 返回的数据格式不正确: {response_data}")
                    break
            except Exception as e:
                if str(e) == "TOKEN_EXPIRED" and retry_count < max_retries:
                    retry_count += 1
                    logger.warning(f"令牌已过期，正在进行第 {retry_count} 次重试")
                    continue
                else:
                    logger.error(f"获取对象 {object_api_name} 数据时发生错误: {str(e)}")
                    break
        
        return {
            "dataList": all_data,
            "total": total
        }
            
    def fetch_multiple_objects_data(self, object_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取多个对象的数据
        
        Args:
            object_configs: 对象配置列表，每个配置包含：
                - object_api_name: 对象API名称
                - filters: 过滤条件列表
                - orders: 排序条件列表
                - limit: 最大获取记录数
                
        Returns:
            Dict[str, Any]: 包含所有对象数据的字典
        """
        result = {}
        total_records = 0
        
        def fetch_single_object(config: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
            """获取单个对象的数据
            
            Args:
                config: 对象配置
                
            Returns:
                tuple[str, Dict[str, Any]]: (对象API名称, 对象数据)
            """
            object_api_name = config["object_api_name"]
            filters = config.get("filters", [])
            orders = config.get("orders", [])
            limit = config.get("limit", 100)
            
            try:
                logger.info(f"开始获取对象 {object_api_name} 的数据")
                # 创建新的服务实例
                fxk_service = FxkService()
                api_client = FxkApiClient()
                custom_object_service = CustomObjectService(fxk_service=fxk_service, api_client=api_client)
                
                # 创建新的 Redis 客户端实例
                redis_client = RedisClient()
                cached_token = redis_client.get(TOKEN_CACHE_KEY)
                if cached_token:
                    logger.info("从Redis缓存中获取企业访问令牌")
                    custom_object_service.set_corp_access_token(cached_token)
                else:
                    # 预先获取企业访问令牌
                    corp_access_token = fxk_service.get_corp_access_token()
                    logger.info("已预先获取企业访问令牌")
                    custom_object_service.set_corp_access_token(corp_access_token)
                    # 将新的令牌存入Redis
                    redis_client.set(TOKEN_CACHE_KEY, corp_access_token)
                
                # 获取对象数据
                object_data = self.fetch_object_data(
                    object_api_name=object_api_name,
                    filters=filters,
                    orders=orders,
                    limit=limit,
                    custom_object_service=custom_object_service
                )
                logger.info(f"成功获取对象 {object_api_name} 的数据，共 {object_data.get('total', 0)} 条记录")
                return object_api_name, object_data
            except Exception as e:
                logger.error(f"获取对象 {object_api_name} 数据失败: {str(e)}")
                return object_api_name, {
                    "dataList": [],
                    "total": 0
                }
        
        logger.info(f"开始并行获取 {len(object_configs)} 个对象的数据")
        # 使用线程池并行获取数据
        with ThreadPoolExecutor(max_workers=min(len(object_configs), 5)) as executor:
            logger.info(f"创建线程池，最大工作线程数: {min(len(object_configs), 5)}")
            # 提交所有任务
            future_to_config = {
                executor.submit(fetch_single_object, config): config 
                for config in object_configs
            }
            logger.info(f"已提交所有 {len(future_to_config)} 个任务")
            
            # 获取结果
            for future in as_completed(future_to_config):
                object_api_name, object_data = future.result()
                result[object_api_name] = object_data
                total_records += object_data.get("total", 0)
                logger.info(f"已完成对象 {object_api_name} 的数据处理")
                
        logger.info(f"所有对象数据处理完成，共处理 {total_records} 条记录")
        return result 