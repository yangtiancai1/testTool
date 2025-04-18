import os
import sys
import logging
from dotenv import load_dotenv
from typing import List, Dict, Any
from utils.redis_client import RedisClient
from config import TOKEN_CACHE_KEY, USER_ID_CACHE_KEY
import json
from datetime import datetime
import shutil
import re

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.custom_object_data_service import CustomObjectDataService
from services.custom_object_service import CustomObjectService
from services.fxk_service import FxkService
from services.custom_object_data_filter_service import CustomObjectDataFilterService
from utils.fxk_api_client import FxkApiClient
from services.report_generation_service import ReportGenerationService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_logging():
    """设置日志配置"""
    # 创建logs目录
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    # 创建文件处理器
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/custom_object_data_{timestamp}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 设置日志格式
    formatter = logging.Formatter('%(asctime)s - [线程 %(thread)d] - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器到logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logger.info(f"日志文件已创建: {log_file}")

def fetch_multiple_objects_data(mobile: str, version: str) -> Dict[str, Dict]:
    """获取多个对象的数据
    
    Args:
        mobile: 手机号
        version: 版本号
        
    Returns:
        Dict[str, Dict]: 对象数据字典
    """
    # 创建服务实例
    data_service = CustomObjectDataService(mobile=mobile)
    
    # 定义多个对象的配置
    object_configs = [
        {
            "object_api_name": "object_tL7xk__c",
            "fields": ["field_854q8__c__r", "field_B79Io__c", "field_LVUI2__c", "field_eX1fb__c"],
            "filters": [
                {
                    "field_name": "field_854q8__c.name",
                    "field_values": [version],
                    "operator": "LIKE",
                    "filterGroup": "1"
                }
            ],
            "orders": [
                {
                    "field_name": "create_time",
                    "is_asc": False
                }
            ],
            "limit": 100
        },
        {
            "object_api_name": "object_notes__c",
            "fields": ["field_2fY70__c__r", "field_2rMd8__c__r", "display_name", "field_s1Ovl__c"],
            "filters": [
                {
                    "field_name": "field_2fY70__c.name",
                    "field_values": [version],
                    "operator": "EQ"
                }
            ],
            "orders": [
                {
                    "field_name": "create_time",
                    "is_asc": False
                }
            ],
            "limit": 100
        },
        {
            "object_api_name": "offline_bug__c",
            "fields": ["dev_team__c__r", "version__c", "severity__c", "status__c", "platform__c", "fixer__c"],
            "filters": [
                {
                    "field_name": "version__c",
                    "field_values": [version],
                    "operator": "EQ"
                },
                {
                    "field_name":"status__c",
                    "field_values":["已解决","新","已关闭"],
                    "operator":"IN",
                    "filterGroup":"1"
                 }
            ],
            "orders": [
                {
                    "field_name": "create_time",
                    "is_asc": False
                }
            ],
            "limit": 100
        }
    ]
    
    # 先获取object_tL7xk__c对象数据，用于解析灰度发布时间
    tL7xk_config = object_configs[0]
    tL7xk_data = data_service.fetch_object_data(
        object_api_name=tL7xk_config["object_api_name"],
        filters=tL7xk_config.get("filters", []),
        orders=tL7xk_config.get("orders", []),
        limit=tL7xk_config.get("limit", 100)
    )
    
    # 解析灰度发布时间
    gray_start_timestamp = None
    full_release_timestamp = None
    
    if tL7xk_data and "dataList" in tL7xk_data and tL7xk_data["dataList"]:
        schedule_text = tL7xk_data["dataList"][0].get("field_eX1fb__c", "")
        if schedule_text:
            # 将文本按行分割并清理每行的空白字符
            lines = [line.strip() for line in schedule_text.split('\n')]
            
            # 解析灰度开始时间（第一次灰度发布时间）
            for line in lines:
                gray_start_match = re.search(r"(\d{4}\.\d{2}\.\d{2})日[夜晚]?\s*灰度", line)
                if gray_start_match:
                    gray_start_str = gray_start_match.group(1)
                    gray_start = datetime.strptime(gray_start_str, "%Y.%m.%d")
                    # 转换为毫秒时间戳
                    gray_start_timestamp = int(gray_start.timestamp() * 1000)
                    break
            
            # 解析全网发布时间
            for line in lines:
                full_release_match = re.search(r"(\d{4}\.\d{2}\.\d{2})日\s*(?:24:00)?\s*全网发布", line)
                if full_release_match:
                    full_release_str = full_release_match.group(1)
                    full_release = datetime.strptime(full_release_str, "%Y.%m.%d")
                    # 转换为毫秒时间戳
                    full_release_timestamp = int(full_release.timestamp() * 1000)
                    break
    
    # 添加object_y31e4__c对象配置
    y31e4_config = {
        "object_api_name": "object_y31e4__c",
        "fields": ["create_time", "field_e89lo__c", "field_NFx1O__c__o"],
        "filters": [
            {"field_name":"field_NFx1O__c",
             "field_values":["225fMwYOT"],
             "operator":"EQ",
             "filterGroup":"1"
            },
            {"field_name":"field_e89lo__c",
             "field_values":[
                "option3IXps861j",
                "optionX8hroekK3",
                "IXav3esg0",
                "KSvf9wzu0",
                "W2jhz498d",
                "Mfkv9c5YS",
                "optioncL4VO9v13"],
                "operator":"HASANYOF",
                "filterGroup":"1"
            }
        ],
        "orders": [
            {
                "field_name": "create_time",
                "is_asc": False
            }
        ],
        "limit": 100
    }
    
    # 如果成功解析了灰度发布时间，添加到查询条件中
    if gray_start_timestamp is not None and full_release_timestamp is not None:
        y31e4_config["filters"].append({
            "field_name": "create_time",
            "field_values": [gray_start_timestamp, full_release_timestamp],
            "operator": "BETWEEN",
            "filterGroup": "1"
        })
    
    # 将object_y31e4__c配置添加到对象配置列表中
    object_configs.append(y31e4_config)
    
    # 添加其他对象配置
    object_configs.extend([
        {
            "object_api_name": "object_0yrBp__c",
            "fields": ["display_name", "field_W6W5T__c", "field_msrO4__c", "field_r83nv__c__r", "field_3ugLn__c__r"],
            "filters": [
                {
                    "field_name": "field_r83nv__c.name",
                    "field_values": [version],
                    "operator": "LIKE"
                }
            ],
            "orders": [
                {
                    "field_name": "create_time",
                    "is_asc": False
                }
            ],
            "limit": 100
        },
        {
            "object_api_name": "object_xkBG2__c",
            "fields": ["field_Xig8k__c", "field_Umnl2__c", "display_name"],
            "filters": [
                {
                    "field_name": "field_r83nv__c.name",
                    "field_values": [version],
                    "operator": "LIKE"
                }
            ],
            "orders": [
                {
                    "field_name": "create_time",
                    "is_asc": False
                }
            ],
            "limit": 100
        }
    ])
    
    # 获取所有对象的数据
    return data_service.fetch_multiple_objects_data(object_configs)

def filter_object_data(raw_results: Dict[str, Dict]) -> Dict[str, Dict]:
    """过滤对象数据，只保留指定字段
    
    Args:
        raw_results: 原始数据结果
        
    Returns:
        Dict[str, Dict]: 过滤后的数据结果
    """
    # 创建过滤器实例
    filter_service = CustomObjectDataFilterService(version="9.5.0")
    
    # 过滤每个对象的数据
    filtered_results = {}
    for object_api_name, result in raw_results.items():
        filtered_results[object_api_name] = filter_service.filter_object_data({object_api_name: result})
    
    return filtered_results

def save_results_to_file(results: Dict[str, Dict], version: str) -> str:
    """将查询结果保存到文件
    
    Args:
        results: 查询结果
        version: 版本号
        
    Returns:
        str: 保存的文件路径
    """
    # 创建输出目录
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"object_data_{version}_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    # 保存数据到文件
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"数据已保存到文件: {filepath}")
    return filepath

def main():
    """主函数"""
    # 设置日志
    setup_logging()
    
    # 清理并重新创建日志和输出目录
    if os.path.exists("logs"):
        shutil.rmtree("logs")
    if os.path.exists("output"):
        shutil.rmtree("output")
    os.makedirs("logs")
    os.makedirs("output")
    logger.info("已清理并重新创建日志和输出目录")
    
    try:
        # 检查是否提供了版本号参数
        if len(sys.argv) < 2:
            logger.error("未提供版本号参数")
            return
            
        # 获取版本号
        version = sys.argv[1]
        logger.info(f"使用版本号: {version}")
        
        # 加载环境变量
        load_dotenv()
        
        # 获取测试手机号
        mobile = os.getenv("TEST_MOBILE")
        if not mobile:
            logger.error("未设置TEST_MOBILE环境变量")
            return
            
        # 初始化服务
        data_service = CustomObjectDataService(mobile=mobile)
        filter_service = CustomObjectDataFilterService(version=version)
        report_service = ReportGenerationService()
        
        # 获取数据
        logger.info("开始获取数据...")
        raw_data = fetch_multiple_objects_data(mobile, version)
        
        # 过滤数据
        logger.info("开始过滤数据...")
        filtered_data = filter_service.filter_object_data(raw_data)
        
        # 保存原始结果
        logger.info("开始保存原始数据...")
        raw_data_file = save_results_to_file(filtered_data, version)
        logger.info(f"原始数据已保存到：{raw_data_file}")
        
        # 生成分析报告
        logger.info("开始生成分析报告...")
        report_file = report_service.generate_and_save_report(filtered_data, version)
        logger.info(f"分析报告已保存到：{report_file}")
        
        logger.info("数据处理和分析完成")
        
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")
        raise

if __name__ == "__main__":
    main() 