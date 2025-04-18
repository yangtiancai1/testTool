import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class CustomObjectDataFilterService:
    """自定义对象数据过滤服务，用于从原始数据中提取指定字段"""
    
    def __init__(self, version: str = None):
        """初始化服务
        
        Args:
            version: 版本号，用于过滤特定版本的数据
        """
        self.version = version
    
    def filter_object_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """过滤对象数据，只保留指定字段
        
        Args:
            raw_data: 原始数据，包含多个对象的数据
            
        Returns:
            Dict[str, Any]: 过滤后的数据，只包含指定字段
        """
        filtered_data = {}
        
        try:
            # 过滤产品发布清单
            if "object_notes__c" in raw_data:
                if isinstance(raw_data["object_notes__c"], dict) and "object_notes__c" in raw_data["object_notes__c"]:
                    filtered_data["object_notes__c"] = self._filter_product_release_notes(raw_data["object_notes__c"]["object_notes__c"])
                else:
                    logger.warning(f"object_notes__c 数据结构不符合预期: {raw_data['object_notes__c']}")
                    filtered_data["object_notes__c"] = self._filter_product_release_notes(raw_data["object_notes__c"])
                
            # 过滤产品发布计划
            if "object_tL7xk__c" in raw_data:
                if isinstance(raw_data["object_tL7xk__c"], dict) and "object_tL7xk__c" in raw_data["object_tL7xk__c"]:
                    filtered_data["object_tL7xk__c"] = self._filter_product_release_plan(raw_data["object_tL7xk__c"]["object_tL7xk__c"])
                else:
                    logger.warning(f"object_tL7xk__c 数据结构不符合预期: {raw_data['object_tL7xk__c']}")
                    filtered_data["object_tL7xk__c"] = self._filter_product_release_plan(raw_data["object_tL7xk__c"])
                
            # 过滤离线BUG
            if "offline_bug__c" in raw_data:
                if isinstance(raw_data["offline_bug__c"], dict) and "offline_bug__c" in raw_data["offline_bug__c"]:
                    filtered_data["offline_bug__c"] = self._filter_offline_bug(raw_data["offline_bug__c"]["offline_bug__c"])
                else:
                    logger.warning(f"offline_bug__c 数据结构不符合预期: {raw_data['offline_bug__c']}")
                    filtered_data["offline_bug__c"] = self._filter_offline_bug(raw_data["offline_bug__c"])
                
            # 过滤系统BUG
            if "object_y31e4__c" in raw_data:
                filtered_data["object_y31e4__c"] = raw_data["object_y31e4__c"]
                
            # 过滤业务模块与相关负责人
            if "object_xkBG2__c" in raw_data:
                if isinstance(raw_data["object_xkBG2__c"], dict) and "object_xkBG2__c" in raw_data["object_xkBG2__c"]:
                    filtered_data["object_xkBG2__c"] = self._filter_business_module(raw_data["object_xkBG2__c"]["object_xkBG2__c"])
                else:
                    logger.warning(f"object_xkBG2__c 数据结构不符合预期: {raw_data['object_xkBG2__c']}")
                    filtered_data["object_xkBG2__c"] = self._filter_business_module(raw_data["object_xkBG2__c"])
                
            # 过滤研发迭代
            if "object_0yrBp__c" in raw_data:
                if isinstance(raw_data["object_0yrBp__c"], dict) and "object_0yrBp__c" in raw_data["object_0yrBp__c"]:
                    filtered_data["object_0yrBp__c"] = self._filter_development_iteration(raw_data["object_0yrBp__c"]["object_0yrBp__c"])
                else:
                    logger.warning(f"object_0yrBp__c 数据结构不符合预期: {raw_data['object_0yrBp__c']}")
                    filtered_data["object_0yrBp__c"] = self._filter_development_iteration(raw_data["object_0yrBp__c"])
                
        except Exception as e:
            logger.error(f"过滤数据时发生错误: {str(e)}")
            logger.error(f"原始数据结构: {raw_data}")
            raise
            
        return filtered_data
    
    def _filter_product_release_notes(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """过滤产品发布清单数据
        
        保留字段：
        - 发布版本【field_2fY70__c__r】
        - 业务模块（单选）【field_2rMd8__c__r】
        - 功能简述【display_name】
        - 一级应用【field_s1Ovl__c】
        """
        if "dataList" not in data:
            return data
            
        filtered_records = []
        for record in data["dataList"]:
            # 检查记录是否为字典类型
            if not isinstance(record, dict):
                logger.warning(f"跳过非字典类型的记录: {record}")
                continue
                
            filtered_record = {
                "field_2fY70__c__r": record.get("field_2fY70__c__r"),
                "field_2rMd8__c__r": record.get("field_2rMd8__c__r"),
                "display_name": record.get("display_name"),
                "field_s1Ovl__c": record.get("field_s1Ovl__c")
            }
            filtered_records.append(filtered_record)
            
        return {
            "dataList": filtered_records,
            "total": data.get("total", 0)
        }
    
    def _filter_product_release_plan(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """过滤产品发布计划数据
        
        保留字段：
        - 版本号 【field_854q8__c__r】
        - 计划开始日期【field_B79Io__c】
        - 计划全网日期【field_LVUI2__c】
        - 发布计划【field_eX1fb__c】
        """
        if "dataList" not in data:
            return data
            
        filtered_records = []
        for record in data["dataList"]:
            # 检查记录是否为字典类型
            if not isinstance(record, dict):
                logger.warning(f"跳过非字典类型的记录: {record}")
                continue
                
            filtered_record = {
                "field_854q8__c__r": record.get("field_854q8__c__r"),
                "field_B79Io__c": record.get("field_B79Io__c"),
                "field_LVUI2__c": record.get("field_LVUI2__c"),
                "field_eX1fb__c": record.get("field_eX1fb__c")
            }
            filtered_records.append(filtered_record)
            
        return {
            "dataList": filtered_records,
            "total": data.get("total", 0)
        }
    
    def _filter_offline_bug(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """过滤线下BUG数据
        
        保留字段：
        - 所属团队【dev_team__c__r】
        - 发现版本【version__c】
        - 严重程度【severity__c】
        - 状态【status__c】
        - 软件平台 【platform__c】
        - 修复人【fixer__c】
        """
        if "dataList" not in data:
            return data
            
        filtered_records = []
        for record in data["dataList"]:
            # 检查记录是否为字典类型
            if not isinstance(record, dict):
                logger.warning(f"跳过非字典类型的记录: {record}")
                continue
                
            filtered_record = {
                "dev_team__c__r": record.get("dev_team__c__r"),
                "version__c": record.get("version__c"),
                "severity__c": record.get("severity__c"),
                "status__c": record.get("status__c"),
                "platform__c": record.get("platform__c"),
                "fixer__c": record.get("fixer__c")
            }
            filtered_records.append(filtered_record)
            
        return {
            "dataList": filtered_records,
            "total": data.get("total", 0)
        }
    
    def _filter_business_module(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """过滤业务模块与相关负责人数据
        
        保留字段：
        - field_Xig8k__c (将value转换为对应的label)
        - field_Umnl2__c
        - display_name
        """
        if "dataList" not in data:
            return data
            
        # 定义value到label的映射
        team_mapping = {
            "mf2w581b9": "售前业务",
            "J31lrQBF9": "售中团队",
            "a25gjoFow": "BI团队",
            "MoDiSmy9D": "流程团队",
            "oJm5at7cp": "元数据权限组",
            "VPr9pd4rj": "基础业务组",
            "j2kkkK7ld": "协同业务团队",
            "t86Lg16yX": "开发平台",
            "J1iwXwS27": "Android架构组",
            "uNEX4Avos": "IOS架构组",
            "64z15xfrq": "Web架构组",
            "zja0v1v2Z": "平台架构组",
            "hxHc3oCd2": "开平对接团队",
            "eBfF20Bqt": "运维团队",
            "mW3r8jMm0": "H5团队",
            "5da2h9kzK": "快消团队",
            "g6va4BIcd": "制造行业组",
            "T6gwWa11D": "互联平台组",
            "gYo1fCe3W": "订货业务组",
            "4i32oGHp5": "集成平台组",
            "Ly2lfhRW1": "营销业务组",
            "P1pt939hl": "大数据团队",
            "W2aZy5G8y": "深圳研发团队",
            "other": "其他团队"
        }
            
        filtered_records = []
        for record in data["dataList"]:
            # 检查记录是否为字典类型
            if not isinstance(record, dict):
                logger.warning(f"跳过非字典类型的记录: {record}")
                continue
                
            # 跳过field_Umnl2__c为null的记录
            if record.get("field_Umnl2__c") is None:
                continue
                
            # 获取field_Xig8k__c的值并转换为label
            field_value = record.get("field_Xig8k__c", "")
            field_label = team_mapping.get(field_value, field_value)  # 如果找不到映射，保留原值
                
            filtered_record = {
                "field_Xig8k__c": field_label,  # 使用转换后的label
                "field_Umnl2__c": record.get("field_Umnl2__c"),
                "display_name": record.get("display_name")
            }
            filtered_records.append(filtered_record)
            
        return {
            "dataList": filtered_records,
            "total": data.get("total", 0)
        }
    
    def _filter_development_iteration(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """过滤研发迭代数据
        
        保留字段：
        - 迭代名称【display_name】
        - TAPD项目ID【field_W6W5T__c】
        - TAPD迭代ID【field_msrO4__c】
        - 所属版本【field_r83nv__c__r】
        - 所属团队【field_3ugLn__c__r】
        """
        if "dataList" not in data:
            return data
            
        filtered_records = []
        for record in data["dataList"]:
            # 检查记录是否为字典类型
            if not isinstance(record, dict):
                logger.warning(f"跳过非字典类型的记录: {record}")
                continue
                
            filtered_record = {
                "display_name": record.get("display_name"),
                "field_W6W5T__c": record.get("field_W6W5T__c"),
                "field_msrO4__c": record.get("field_msrO4__c"),
                "field_r83nv__c__r": record.get("field_r83nv__c__r"),
                "field_3ugLn__c__r": record.get("field_3ugLn__c__r")
            }
            filtered_records.append(filtered_record)
            
        return {
            "dataList": filtered_records,
            "total": data.get("total", 0)
        } 