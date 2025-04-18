from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class ICustomObjectService(ABC):
    """自定义对象服务接口"""
    
    @abstractmethod
    def set_corp_access_token(self, corp_access_token: str) -> None:
        """设置企业访问令牌
        
        Args:
            corp_access_token: 企业访问令牌
        """
        pass
    
    @abstractmethod
    def query_custom_objects(self, 
                            data_object_api_name: str, 
                            mobile: str,
                            limit: int = 10, 
                            offset: int = 0,
                            filters: Optional[List[Dict[str, Any]]] = None,
                            orders: Optional[List[Dict[str, Any]]] = None,
                            find_explicit_total_num: str = "true") -> Dict[str, Any]:
        """查询自定义对象列表
        
        Args:
            data_object_api_name: 对象的api_name，例如：DeliveryNoteProductObj
            mobile: 当前用户的手机号，用于获取用户ID
            limit: 分页条数(最大值为100)
            offset: 偏移量(从0开始、数值必须为limit的整数倍)
            filters: 过滤条件列表，可选，默认为空列表
            orders: 排序条件列表，可选，默认为按创建时间降序
            find_explicit_total_num: 是否返回总数(true:返回total总数,false:不返回total总数)
            
        Returns:
            Dict[str, Any]: 包含自定义对象列表的响应
        """
        pass
    
    @abstractmethod
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
        """
        pass 