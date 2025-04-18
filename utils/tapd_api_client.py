import requests
from typing import Dict, Any, Optional
from datetime import datetime

class TapdApiClient:
    """TAPD API客户端"""
    
    def __init__(self, api_user: str, api_password: str):
        """初始化TAPD API客户端
        
        Args:
            api_user: TAPD API用户名
            api_password: TAPD API密码
        """
        self.api_user = "fxiaoke"
        self.api_password = "07ECB7C8-9492-C6E4-79FC-3D45AC634FXK"
        self.base_url = "https://api.tapd.cn"
        
    def get_stories_count(self, workspace_id: int, **kwargs) -> Optional[int]:
        """获取符合查询条件的需求数量
        
        Args:
            workspace_id: 项目ID
            **kwargs: 其他查询参数，支持以下字段：
                - id: 需求ID
                - name: 标题
                - priority_label: 优先级
                - business_value: 业务价值
                - status: 状态
                - label: 标签
                - version: 版本
                - module: 模块
                - test_focus: 测试重点
                - size: 规模
                - owner: 处理人
                - cc: 抄送人
                - creator: 创建人
                - developer: 开发人员
                - begin: 预计开始时间
                - due: 预计结束时间
                - created: 创建时间
                - modified: 最后修改时间
                - completed: 完成时间
                - iteration_id: 迭代ID
                - effort: 预估工时
                - effort_completed: 完成工时
                - remain: 剩余工时
                - exceed: 超出工时
                - category_id: 需求分类
                - workitem_type_id: 需求类别ID
                - release_id: 发布计划ID
                - source: 来源
                - type: 类型
                - parent_id: 父需求ID
                - children_id: 子需求ID
                - description: 详细描述
                - custom_field_*: 自定义字段
                - custom_plan_field_*: 自定义计划应用字段
                
        Returns:
            Optional[int]: 需求数量，如果请求失败则返回None
        """
        url = f"{self.base_url}/stories/count"
        
        # 构建查询参数
        params = {"workspace_id": workspace_id}
        
        # 添加其他查询参数
        for key, value in kwargs.items():
            if value is not None:
                # 处理日期时间类型
                if isinstance(value, datetime):
                    value = value.strftime("%Y-%m-%d %H:%M:%S")
                params[key] = value
                
        try:
            response = requests.get(
                url,
                params=params,
                auth=(self.api_user, self.api_password)
            )
            response.raise_for_status()
            
            data = response.json()
            if data["status"] == 1:
                return data["data"]["count"]
            return None
            
        except Exception as e:
            print(f"获取需求数量失败: {str(e)}")
            return None 

    def get_bugs_count(self, workspace_id: int, **kwargs) -> Optional[int]:
        """获取符合查询条件的需求数量
        
        Args:
            workspace_id: 项目ID
            **kwargs: 其他查询参数，支持以下字段：
                - id: 需求ID
                - name: 标题
                - priority_label: 优先级
                - business_value: 业务价值
                - status: 状态
                - label: 标签
                - version: 版本
                - module: 模块
                - test_focus: 测试重点
                - size: 规模
                - owner: 处理人
                - cc: 抄送人
                - creator: 创建人
                - developer: 开发人员
                - begin: 预计开始时间
                - due: 预计结束时间
                - created: 创建时间
                - modified: 最后修改时间
                - completed: 完成时间
                - iteration_id: 迭代ID
                - effort: 预估工时
                - effort_completed: 完成工时
                - remain: 剩余工时
                - exceed: 超出工时
                - category_id: 需求分类
                - workitem_type_id: 需求类别ID
                - release_id: 发布计划ID
                - source: 来源
                - type: 类型
                - parent_id: 父需求ID
                - children_id: 子需求ID
                - description: 详细描述
                - custom_field_*: 自定义字段
                - custom_plan_field_*: 自定义计划应用字段
                
        Returns:
            Optional[int]: 需求数量，如果请求失败则返回None
        """
        url = f"{self.base_url}/bugs/count"
        
        # 构建查询参数
        params = {"workspace_id": workspace_id}
        
        # 添加其他查询参数
        for key, value in kwargs.items():
            if value is not None:
                # 处理日期时间类型
                if isinstance(value, datetime):
                    value = value.strftime("%Y-%m-%d %H:%M:%S")
                params[key] = value
                
        print(f"TAPD API请求URL: {url}")
        print(f"TAPD API请求参数: {params}")
        
        try:
            response = requests.get(
                url,
                params=params,
                auth=(self.api_user, self.api_password)
            )
            response.raise_for_status()
            
            print(f"TAPD API响应状态码: {response.status_code}")
            print(f"TAPD API响应内容: {response.text}")
            
            data = response.json()
            if data["status"] == 1:
                return data["data"]["count"]
            return None
            
        except Exception as e:
            print(f"获取需求数量失败: {str(e)}")
            return None 