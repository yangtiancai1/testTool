from typing import Dict, Any
from .http_client import HttpClient
from config import (
    FXK_API_BASE_URL, FXK_APP_ID, FXK_APP_SECRET,
    FXK_PERMANENT_CODE
)
import urllib.parse

class FxkApiClient:
    def __init__(self):
        self.http_client = HttpClient()
        self.base_url = FXK_API_BASE_URL
        self._corp_id = None

    def _validate_config(self):
        """验证配置是否完整"""
        missing_configs = []
        if not FXK_APP_ID:
            missing_configs.append("FXK_APP_ID")
        if not FXK_APP_SECRET:
            missing_configs.append("FXK_APP_SECRET")
        if not FXK_PERMANENT_CODE:
            missing_configs.append("FXK_PERMANENT_CODE")
        
        if missing_configs:
            raise ValueError(f"缺少必要的配置项: {', '.join(missing_configs)}")

    def get_corp_access_token(self) -> Dict[str, Any]:
        """获取企业访问令牌"""
        # 验证配置
        self._validate_config()
        
        url = f"{self.base_url}/corpAccessToken/get/V2"
        data = {
            "appId": FXK_APP_ID,
            "appSecret": FXK_APP_SECRET,
            "permanentCode": FXK_PERMANENT_CODE
        }
        return self.http_client.post(url, data)

    def get_corp_id(self) -> str:
        """获取企业ID"""
        if self._corp_id:
            return self._corp_id
            
        response = self.get_corp_access_token()
        if response.is_success():
            self._corp_id = response.get_data('corpId')
            if not self._corp_id:
                raise ValueError("获取企业ID失败：响应中未包含corpId")
            return self._corp_id
        raise ValueError(f"获取企业ID失败: {response.message}")

    def get_user_id_by_mobile(self, corp_access_token: str, mobile: str, corp_id: str = None) -> Dict[str, Any]:
        """根据手机号获取用户ID
        
        Args:
            corp_access_token: 企业访问令牌
            mobile: 手机号
            corp_id: 企业ID，可选，如果不提供则自动获取
            
        Returns:
            Dict[str, Any]: 包含用户信息的响应
        """
        # 验证参数
        if not corp_access_token:
            raise ValueError("corp_access_token不能为空")
        if not mobile:
            raise ValueError("mobile不能为空")
        
        # 获取企业ID（如果未提供）
        if not corp_id:
            corp_id = self.get_corp_id()
        
        url = f"{self.base_url}/user/getByMobile"
        data = {
            "corpAccessToken": corp_access_token,
            "corpId": corp_id,
            "mobile": mobile
        }
        return self.http_client.post(url, data)

    
    def query_custom_object(self, corp_access_token: str, current_open_user_id: str, data_object_api_name: str, 
                           search_query_info: Dict[str, Any], find_explicit_total_num: str = "true", 
                           corp_id: str = None) -> Dict[str, Any]:
        """查询自定义对象列表
        
        Args:
            corp_access_token: 企业访问令牌
            current_open_user_id: 当前用户ID
            data_object_api_name: 对象的api_name，固定取值：DeliveryNoteProductObj
            search_query_info: 查询条件
                - limit: 分页条数(最大值为100)
                - offset: 偏移量(从0开始、数值必须为limit的整数倍)
                - filters: 过滤条件列表
                    - field_name: 字段名
                    - field_values: 字段值
                    - operator: 操作符
                - orders: 排序
                    - fieldName: 字段名
                    - isAsc: 是否升序
            find_explicit_total_num: 是否返回总数(true:返回total总数,false:不返回total总数)
            corp_id: 企业ID，可选，如果不提供则自动获取
            
        Returns:
            Dict[str, Any]: 包含自定义对象列表的响应
            
        Note:
            操作符说明:
            - EQ: =
            - GT: >
            - LT: <
            - GTE: >=
            - LTE: <=
            - N: <>
            - LIKE: LIKE
            - NLIKE: NOT LIKE
            - IS: IS
            - ISN: IS NOT
            - IN: IN
            - NIN: NOT IN
            - BETWEEN: BETWEEN
            - NBETWEEN: NOT BETWEEN
            - STARTWITH: LIKE%
            - ENDWITH: %LIKE
            - CONTAINS: Array 包含
        """
        # 验证参数
        if not corp_access_token:
            raise ValueError("corp_access_token不能为空")
        if not current_open_user_id:
            raise ValueError("current_open_user_id不能为空")
        if not data_object_api_name:
            raise ValueError("data_object_api_name不能为空")
        if not search_query_info:
            raise ValueError("search_query_info不能为空")
            
        # 验证search_query_info中的必要字段
        required_fields = ["limit", "offset", "filters", "orders"]
        for field in required_fields:
            if field not in search_query_info:
                raise ValueError(f"search_query_info中缺少必要字段: {field}")
                
        # 验证limit和offset
        if not isinstance(search_query_info["limit"], int) or search_query_info["limit"] <= 0 or search_query_info["limit"] > 100:
            raise ValueError("limit必须是1-100之间的整数")
        if not isinstance(search_query_info["offset"], int) or search_query_info["offset"] < 0:
            raise ValueError("offset必须是非负整数")
        if search_query_info["offset"] % search_query_info["limit"] != 0:
            raise ValueError("offset必须是limit的整数倍")
            
        # 获取企业ID（如果未提供）
        if not corp_id:
            corp_id = self.get_corp_id()
            
        url = f"{self.base_url}/crm/custom/v2/data/query"
        data = {
            "corpAccessToken": corp_access_token,
            "currentOpenUserId": current_open_user_id,
            "corpId": corp_id,
            "data": {
                "dataObjectApiName": data_object_api_name,
                "find_explicit_total_num": find_explicit_total_num,
                "search_query_info": search_query_info
            }
        }
        return self.http_client.post(url, data) 