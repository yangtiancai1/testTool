import json
from docxtpl import DocxTemplate
from datetime import datetime
import os
import glob
import subprocess
import sys
from dotenv import load_dotenv

def find_latest_report(output_dir='output'):
    """查找output目录下最新的report文件
    
    Args:
        output_dir: 输出目录路径
        
    Returns:
        str: 最新的report文件路径，如果没有找到则返回None
    """
    # 获取所有report文件
    report_files = glob.glob(os.path.join(output_dir, 'report_*.json'))
    
    if not report_files:
        return None
        
    # 按修改时间排序，获取最新的文件
    latest_file = max(report_files, key=os.path.getmtime)
    return latest_file

def fetch_data_and_generate_report(version):
    """调用custom_object_data_example.py获取数据并生成报告
    
    Args:
        version: 版本号
        
    Returns:
        str: 生成的report文件路径
    """
    try:
        # 获取当前脚本所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 构建custom_object_data_example.py的完整路径
        example_script = os.path.join(current_dir, 'examples', 'custom_object_data_example.py')
        
        # 调用custom_object_data_example.py，并传递版本号参数
        result = subprocess.run(
            [sys.executable, example_script, version],
            capture_output=True,
            text=True,
            check=True
        )
        
        # 查找最新生成的report文件
        report_file = find_latest_report()
        if not report_file:
            raise FileNotFoundError("调用custom_object_data_example.py后未找到生成的report文件")
            
        return report_file
        
    except subprocess.CalledProcessError as e:
        print(f"调用custom_object_data_example.py失败: {str(e)}")
        print(f"错误输出: {e.stderr}")
        raise
    except Exception as e:
        print(f"获取数据时发生错误: {str(e)}")
        raise

def load_json_data(json_file):
    """加载JSON数据"""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_features(features):
    """格式化功能特性列表，添加序号"""
    return [f"{i+1}.{feature}" for i, feature in enumerate(features)]

def format_date(iso_date):
    """将ISO格式的日期转换为中文年月日格式
    
    Args:
        iso_date: ISO格式的日期字符串，如 "2025-04-16T21:28:00.157601"
        
    Returns:
        str: 中文格式的日期字符串，如 "2025年04月16日"
    """
    try:
        dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
        return dt.strftime('%Y年%m月%d日')
    except (ValueError, TypeError):
        return iso_date

def format_test_cycle(test_cycle):
    """格式化测试周期数据，将时间转换为中文格式
    
    Args:
        test_cycle: 测试周期数据字典
        
    Returns:
        dict: 格式化后的测试周期数据
    """
    if not test_cycle:
        return test_cycle
        
    formatted = test_cycle.copy()
    if '开始时间' in formatted:
        formatted['开始时间'] = format_date(formatted['开始时间'])
    if '结束时间' in formatted:
        formatted['结束时间'] = format_date(formatted['结束时间'])
    return formatted

def calculate_critical_bugs(bug_stats):
    """计算致命和严重bug的总数
    
    Args:
        bug_stats: Bug统计数据结构
        
    Returns:
        int: 致命和严重bug的总数
    """
    if not bug_stats:
        return 0
        
    fatal_total = bug_stats.get('致命', {}).get('total', 0)
    serious_total = bug_stats.get('严重', {}).get('total', 0)
    return fatal_total + serious_total

def calculate_platform_bug_totals(bug_stats):
    """计算各平台各严重程度的bug总数
    
    Args:
        bug_stats: Bug统计数据
        
    Returns:
        dict: 处理后的统计数据，包含各类型bug的总数
    """
    if not bug_stats:
        return {}
        
    # 定义所有平台类型
    platforms = ["Web", "H5", "Server", "小程序", "Android", "iOS"]
    
    result = {}
    for business_line, data in bug_stats.items():
        result[business_line] = {
            "platforms": {},
            "total": data.get("total", 0)  # 业务线总计
        }
        
        # 初始化每个平台的数据结构
        for platform in platforms:
            if platform in data:
                severities = data[platform]
                result[business_line]["platforms"][platform] = {
                    "fatal_total": sum(severities["fatal"].values()),
                    "serious_total": sum(severities["serious"].values()),
                    "normal_total": sum(severities["normal"].values()),
                    "advice_total": sum(severities["advice"].values())
                }
                # 计算平台总计
                result[business_line]["platforms"][platform]["platform_total"] = (
                    result[business_line]["platforms"][platform]["fatal_total"] +
                    result[business_line]["platforms"][platform]["serious_total"] +
                    result[business_line]["platforms"][platform]["normal_total"] +
                    result[business_line]["platforms"][platform]["advice_total"]
                )
                
        # 计算各严重程度的业务线总计
        result[business_line].update({
            "fatal_total": sum(p["fatal_total"] for p in result[business_line]["platforms"].values()),
            "serious_total": sum(p["serious_total"] for p in result[business_line]["platforms"].values()),
            "normal_total": sum(p["normal_total"] for p in result[business_line]["platforms"].values()),
            "advice_total": sum(p["advice_total"] for p in result[business_line]["platforms"].values())
        })
            
    return result

def calculate_development_quality(bug_stats):
    """计算开发质量统计
    
    Args:
        bug_stats: Bug统计数据
        
    Returns:
        dict: 处理后的开发质量统计数据，包含开发人数、缺陷数和质量指标
    """
    if not bug_stats:
        return {}
        
    # 定义所有平台类型
    platforms = ["Web", "H5", "Server", "小程序", "Android", "iOS"]
    
    result = {}
    for business_line, data in bug_stats.items():
        result[business_line] = {
            "platforms": {},
            "total_bugs": 0,
            "total_devs": 0,
            "quality": 0
        }
        
        total_bugs = 0
        total_devs = set()  # 用于去重统计总开发人数
        
        # 处理每个平台的数据
        for platform in platforms:
            if platform in data:
                platform_devs = set()  # 用于统计平台开发人数
                platform_bugs = 0
                
                # 统计平台的bug数
                severities = data[platform]
                for severity_type in ["fatal", "serious", "normal", "advice"]:
                    severity_data = severities.get(severity_type, {})
                    for status in ["新", "已解决", "已关闭"]:
                        bug_count = severity_data.get(status, 0)
                        platform_bugs += bug_count
                
                # 收集该平台所有bug的开发人员信息，并去重
                for bug in data.get("bugs", []):
                    if bug.get("platform__c") == platform:
                        fixers = bug.get("fixer__c", [])
                        if isinstance(fixers, list):
                            platform_devs.update(fixers)  # 使用set自动去重
                
                # 更新平台统计数据
                dev_count = len(platform_devs)
                result[business_line]["platforms"][platform] = {
                    "dev_count": dev_count,
                    "bug_count": platform_bugs,
                    "quality": round(platform_bugs / dev_count, 2) if dev_count > 0 else 0
                }
                
                # 更新业务线总计
                total_bugs += platform_bugs
                total_devs.update(platform_devs)  # 使用set自动去重
            else:
                # 如果平台数据不存在，设置默认值
                result[business_line]["platforms"][platform] = {
                    "dev_count": 0,
                    "bug_count": 0,
                    "quality": 0
                }
        
        # 更新业务线统计数据
        result[business_line]["total_bugs"] = total_bugs
        result[business_line]["total_devs"] = len(total_devs)  # 使用set的长度作为去重后的开发人数
        if result[business_line]["total_devs"] > 0:
            result[business_line]["quality"] = round(
                total_bugs / result[business_line]["total_devs"],
                2
            )
            
    return result

def find_report_by_version(version, output_dir='output'):
    """根据版本号查找对应的report文件
    
    Args:
        version: 版本号，如 "9.5.0"
        output_dir: 输出目录路径
        
    Returns:
        str: 找到的report文件路径，如果没有找到则返回None
    """
    # 将版本号转换为可能的文件名格式
    version_patterns = [
        version.replace('.', ''),  # 9.5.0 -> 950
        version  # 9.5.0
    ]
    
    # 获取所有report文件
    report_files = glob.glob(os.path.join(output_dir, 'report_*.json'))
    
    # 查找匹配版本号的文件
    for file in report_files:
        filename = os.path.basename(file)
        for pattern in version_patterns:
            if pattern in filename:
                return file
                
    return None

def generate_report(version, json_file=None, output_path=None):
    """生成测试报告
    
    Args:
        version: 版本号，必需参数
        json_file: JSON数据文件路径，如果为None则自动查找最新的report文件
        output_path: 输出文件路径，如果为None则自动生成
        
    Returns:
        str: 生成的报告文件路径
    """
    if not version:
        raise ValueError("版本号不能为空")
    
    # 指定模板文件路径
    template_path = '纷享销客X.X.X测试报告模版.docx'
    
    # 如果没有指定json_file，则查找或生成report文件
    if json_file is None:
        # 查找该版本号对应的report文件
        json_file = find_report_by_version(version)
        if json_file is None:
            print(f"未找到版本 {version} 的report文件，尝试获取新数据...")
            json_file = fetch_data_and_generate_report(version)
            print(f"已生成新的report文件: {json_file}")
        else:
            print(f"找到版本 {version} 的report文件: {json_file}")
    
    # 加载数据
    data = load_json_data(json_file)
    
    # 加载模板
    doc = DocxTemplate(template_path)
    
    # 合并深研团队的功能特性
    deep_research_features = []
    deep_research_teams = [
        '互联平台-互联平台组',
        '集成平台-集成平台组',
        '渠道分销管理-订货业务组',
        '服务管理-制造行业组',
        '营销管理-营销业务组',
        '渠道分销管理-制造行业组',
        '销售管理-订货业务组'
    ]
    
    # 初始化团队功能特性统计
    team_features = data['data'].get('团队功能特性统计', {})
    for team in deep_research_teams:
        if team in team_features:
            deep_research_features.extend(team_features[team].get('features', []))
    
    # 为每个业务线添加功能特性统计标记
    team_features_mark = {
        'sfa_features_mark': '通过' if team_features.get('销售管理-售前业务', {}).get('features') else '',
        'sales_mid_features_mark': '通过' if team_features.get('销售管理-售中团队', {}).get('features') else '',
        'fcm_features_mark': '通过' if team_features.get('快消行业解决方案-快消团队', {}).get('features') else '',
        'deep_research_features_mark': '通过' if deep_research_features else '',
        'channel_features_mark': '通过' if team_features.get('渠道管理-售中团队', {}).get('features') else '',
        'paas_base_features_mark': '通过' if team_features.get('PaaS平台-基础业务组', {}).get('features') else '',
        'paas_collaboration_features_mark': '通过' if team_features.get('PaaS平台-协同业务团队', {}).get('features') else '',
        'paas_metadata_features_mark': '通过' if team_features.get('PaaS平台-元数据权限组', {}).get('features') else '',
        'paas_flow_features_mark': '通过' if team_features.get('PaaS平台-流程团队', {}).get('features') else '',
        'bi_features_mark': '通过' if team_features.get('智能分析平台-BI团队', {}).get('features') else ''
    }
    
    # 准备bug统计数据
    bug_stats_data = {
        'SFA业务线': data['data'].get('团队平台Bug统计', {}).get('SFA业务线', {}),
        'PAAS平台': data['data'].get('团队平台Bug统计', {}).get('PAAS平台', {}),
        '深研业务线': data['data'].get('团队平台Bug统计', {}).get('深研业务线', {}),
        '快消业务线': data['data'].get('团队平台Bug统计', {}).get('快消业务线', {}),
        'BI业务线': data['data'].get('团队平台Bug统计', {}).get('BI业务线', {})
    }
    
    # 确保所有必需的数据结构都存在
    default_features = {'features': []}
    default_stats = {'total': 0}
    
    # 准备上下文数据
    context = {
        'version': data.get('version', version),
        'generate_time': format_date(data.get('generate_time', '')),
        'test_cycle': format_test_cycle(data['data'].get('测试周期', {})),
        'requirement_stats': data['data'].get('需求统计', {'总需求数': 0}),
        'team_features': team_features,
        'bug_stats': data['data'].get('Bug严重程度统计', default_stats),
        'critical_bugs_total': calculate_critical_bugs(data['data'].get('Bug严重程度统计', default_stats)),
        'team_bug_stats': data['data'].get('团队平台Bug统计', {}),
        'gray_bugs': data['data'].get('灰度期间bug数量', 0),
        # 添加所有团队的功能特性（带序号）
        'sfa_features': format_features(team_features.get('销售管理-售前业务', default_features).get('features', [])),
        'sales_mid_features': format_features(team_features.get('销售管理-售中团队', default_features).get('features', [])),
        'fcm_features': format_features(team_features.get('快消行业解决方案-快消团队', default_features).get('features', [])),
        'deep_research_features': format_features(deep_research_features),
        'channel_features': format_features(team_features.get('渠道管理-售中团队', default_features).get('features', [])),
        'paas_base_features': format_features(team_features.get('PaaS平台-基础业务组', default_features).get('features', [])),
        'paas_collaboration_features': format_features(team_features.get('PaaS平台-协同业务团队', default_features).get('features', [])),
        'paas_metadata_features': format_features(team_features.get('PaaS平台-元数据权限组', default_features).get('features', [])),
        'paas_flow_features': format_features(team_features.get('PaaS平台-流程团队', default_features).get('features', [])),
        'bi_features': format_features(team_features.get('智能分析平台-BI团队', default_features).get('features', [])),
        # 添加团队功能特性统计标记
        'sfa_features_mark': team_features_mark['sfa_features_mark'],
        'sales_mid_features_mark': team_features_mark['sales_mid_features_mark'],
        'fcm_features_mark': team_features_mark['fcm_features_mark'],
        'deep_research_features_mark': team_features_mark['deep_research_features_mark'],
        'channel_features_mark': team_features_mark['channel_features_mark'],
        'paas_base_features_mark': team_features_mark['paas_base_features_mark'],
        'paas_collaboration_features_mark': team_features_mark['paas_collaboration_features_mark'],
        'paas_metadata_features_mark': team_features_mark['paas_metadata_features_mark'],
        'paas_flow_features_mark': team_features_mark['paas_flow_features_mark'],
        'bi_features_mark': team_features_mark['bi_features_mark'],
        # 添加业务线统计数据
        'business_line_bug_stats': bug_stats_data,
        'platform_bug_totals': calculate_platform_bug_totals(bug_stats_data),
        # 添加各业务线的开发质量统计数据，并设置默认值
        'sfa_dev_quality': {
            'Web': data['data'].get('开发质量统计', {}).get('SFA业务线', {}).get('Web', {'dev_count': 0, 'bug_count': 0, 'quality': 0}),
            'Server': data['data'].get('开发质量统计', {}).get('SFA业务线', {}).get('Server', {'dev_count': 0, 'bug_count': 0, 'quality': 0}),
            '小程序': data['data'].get('开发质量统计', {}).get('SFA业务线', {}).get('小程序', {'dev_count': 0, 'bug_count': 0, 'quality': 0}),
            'H5': {'dev_count': 0, 'bug_count': 0, 'quality': 0},  # 添加默认值
            'Android': {'dev_count': 0, 'bug_count': 0, 'quality': 0},  # 添加默认值
            'iOS': {'dev_count': 0, 'bug_count': 0, 'quality': 0},  # 添加默认值
            'total': {
                'dev_count': sum(data['data'].get('开发质量统计', {}).get('SFA业务线', {}).get(platform, {}).get('dev_count', 0) 
                              for platform in ['Web', 'Server', '小程序']),
                'bug_count': sum(data['data'].get('开发质量统计', {}).get('SFA业务线', {}).get(platform, {}).get('bug_count', 0) 
                              for platform in ['Web', 'Server', '小程序']),
                'quality': 0
            },
            'best_platform': data['data'].get('开发质量统计', {}).get('SFA业务线', {}).get('best_platform', {
                'platform': '',
                'quality': 0,
                'bug_count': 0,
                'dev_count': 0
            })
        },
        'paas_dev_quality': {
            'Web': data['data'].get('开发质量统计', {}).get('PAAS平台', {}).get('Web', {'dev_count': 0, 'bug_count': 0, 'quality': 0}),
            'Server': data['data'].get('开发质量统计', {}).get('PAAS平台', {}).get('Server', {'dev_count': 0, 'bug_count': 0, 'quality': 0}),
            '小程序': data['data'].get('开发质量统计', {}).get('PAAS平台', {}).get('小程序', {'dev_count': 0, 'bug_count': 0, 'quality': 0}),
            'H5': data['data'].get('开发质量统计', {}).get('PAAS平台', {}).get('H5', {'dev_count': 0, 'bug_count': 0, 'quality': 0}),
            'Android': data['data'].get('开发质量统计', {}).get('PAAS平台', {}).get('Android', {'dev_count': 0, 'bug_count': 0, 'quality': 0}),
            'iOS': data['data'].get('开发质量统计', {}).get('PAAS平台', {}).get('iOS', {'dev_count': 0, 'bug_count': 0, 'quality': 0}),
            'total': {
                'dev_count': sum(data['data'].get('开发质量统计', {}).get('PAAS平台', {}).get(platform, {}).get('dev_count', 0) 
                              for platform in ['Web', 'Server', '小程序', 'H5', 'Android', 'iOS']),
                'bug_count': sum(data['data'].get('开发质量统计', {}).get('PAAS平台', {}).get(platform, {}).get('bug_count', 0) 
                              for platform in ['Web', 'Server', '小程序', 'H5', 'Android', 'iOS']),
                'quality': 0
            },
            'best_platform': data['data'].get('开发质量统计', {}).get('PAAS平台', {}).get('best_platform', {
                'platform': '',
                'quality': 0,
                'bug_count': 0,
                'dev_count': 0
            })
        },
        'deep_research_dev_quality': {
            'Web': data['data'].get('开发质量统计', {}).get('深研业务线', {}).get('Web', {'dev_count': 0, 'bug_count': 0, 'quality': 0}),
            'Server': data['data'].get('开发质量统计', {}).get('深研业务线', {}).get('Server', {'dev_count': 0, 'bug_count': 0, 'quality': 0}),
            '小程序': data['data'].get('开发质量统计', {}).get('深研业务线', {}).get('小程序', {'dev_count': 0, 'bug_count': 0, 'quality': 0}),
            'Android': data['data'].get('开发质量统计', {}).get('深研业务线', {}).get('Android', {'dev_count': 0, 'bug_count': 0, 'quality': 0}),
            'H5（小程序）': data['data'].get('开发质量统计', {}).get('深研业务线', {}).get('H5（小程序）', {'dev_count': 0, 'bug_count': 0, 'quality': 0}),
            'H5': {'dev_count': 0, 'bug_count': 0, 'quality': 0},  # 添加默认值
            'iOS': {'dev_count': 0, 'bug_count': 0, 'quality': 0},  # 添加默认值
            'total': {
                'dev_count': sum(data['data'].get('开发质量统计', {}).get('深研业务线', {}).get(platform, {}).get('dev_count', 0) 
                              for platform in ['Web', 'Server', '小程序', 'Android', 'H5（小程序）']),
                'bug_count': sum(data['data'].get('开发质量统计', {}).get('深研业务线', {}).get(platform, {}).get('bug_count', 0) 
                              for platform in ['Web', 'Server', '小程序', 'Android', 'H5（小程序）']),
                'quality': 0
            },
            'best_platform': data['data'].get('开发质量统计', {}).get('深研业务线', {}).get('best_platform', {
                'platform': '',
                'quality': 0,
                'bug_count': 0,
                'dev_count': 0
            })
        },
        'fcm_dev_quality': {
            'Web': data['data'].get('开发质量统计', {}).get('快消团队', {}).get('Web', {'dev_count': 0, 'bug_count': 0, 'quality': 0}),
            'Server': data['data'].get('开发质量统计', {}).get('快消团队', {}).get('Server', {'dev_count': 0, 'bug_count': 0, 'quality': 0}),
            '小程序': data['data'].get('开发质量统计', {}).get('快消团队', {}).get('小程序', {'dev_count': 0, 'bug_count': 0, 'quality': 0}),
            'H5': data['data'].get('开发质量统计', {}).get('快消团队', {}).get('H5', {'dev_count': 0, 'bug_count': 0, 'quality': 0}),
            'Android': data['data'].get('开发质量统计', {}).get('快消团队', {}).get('Android', {'dev_count': 0, 'bug_count': 0, 'quality': 0}),
            'iOS': data['data'].get('开发质量统计', {}).get('快消团队', {}).get('iOS', {'dev_count': 0, 'bug_count': 0, 'quality': 0}),
            'total': {
                'dev_count': sum(data['data'].get('开发质量统计', {}).get('快消团队', {}).get(platform, {}).get('dev_count', 0) 
                              for platform in ['Web', 'Server', '小程序', 'H5', 'Android', 'iOS']),
                'bug_count': sum(data['data'].get('开发质量统计', {}).get('快消团队', {}).get(platform, {}).get('bug_count', 0) 
                              for platform in ['Web', 'Server', '小程序', 'H5', 'Android', 'iOS']),
                'quality': 0
            },
            'best_platform': data['data'].get('开发质量统计', {}).get('快消团队', {}).get('best_platform', {
                'platform': '',
                'quality': 0,
                'bug_count': 0,
                'dev_count': 0
            })
        },
        'bi_dev_quality': {
            'Web': data['data'].get('开发质量统计', {}).get('BI业务线', {}).get('Web', {'dev_count': 0, 'bug_count': 0, 'quality': 0}),
            'Server': data['data'].get('开发质量统计', {}).get('BI业务线', {}).get('Server', {'dev_count': 0, 'bug_count': 0, 'quality': 0}),
            '小程序': data['data'].get('开发质量统计', {}).get('BI业务线', {}).get('小程序', {'dev_count': 0, 'bug_count': 0, 'quality': 0}),
            'H5': {'dev_count': 0, 'bug_count': 0, 'quality': 0},  # 添加默认值
            'Android': {'dev_count': 0, 'bug_count': 0, 'quality': 0},  # 添加默认值
            'iOS': {'dev_count': 0, 'bug_count': 0, 'quality': 0},  # 添加默认值
            'total': {
                'dev_count': sum(data['data'].get('开发质量统计', {}).get('BI业务线', {}).get(platform, {}).get('dev_count', 0) 
                              for platform in ['Web', 'Server', '小程序']),
                'bug_count': sum(data['data'].get('开发质量统计', {}).get('BI业务线', {}).get(platform, {}).get('bug_count', 0) 
                              for platform in ['Web', 'Server', '小程序']),
                'quality': 0
            },
            'best_platform': data['data'].get('开发质量统计', {}).get('BI业务线', {}).get('best_platform', {
                'platform': '',
                'quality': 0,
                'bug_count': 0,
                'dev_count': 0
            })
        },
        # 添加各业务线的bug数最多的两个平台信息
        'sfa_top_platforms': {
            'first': data['data'].get('团队平台Bug统计', {}).get('SFA业务线', {}).get('top_platforms', {}).get('first', {'platform': '', 'count': 0}),
            'second': data['data'].get('团队平台Bug统计', {}).get('SFA业务线', {}).get('top_platforms', {}).get('second', {'platform': '', 'count': 0})
        },
        'paas_top_platforms': {
            'first': data['data'].get('团队平台Bug统计', {}).get('PAAS平台', {}).get('top_platforms', {}).get('first', {'platform': '', 'count': 0}),
            'second': data['data'].get('团队平台Bug统计', {}).get('PAAS平台', {}).get('top_platforms', {}).get('second', {'platform': '', 'count': 0})
        },
        'deep_research_top_platforms': {
            'first': data['data'].get('团队平台Bug统计', {}).get('深研业务线', {}).get('top_platforms', {}).get('first', {'platform': '', 'count': 0}),
            'second': data['data'].get('团队平台Bug统计', {}).get('深研业务线', {}).get('top_platforms', {}).get('second', {'platform': '', 'count': 0})
        },
        'fcm_top_platforms': {
            'first': data['data'].get('团队平台Bug统计', {}).get('快消业务线', {}).get('top_platforms', {}).get('first', {'platform': '', 'count': 0}),
            'second': data['data'].get('团队平台Bug统计', {}).get('快消业务线', {}).get('top_platforms', {}).get('second', {'platform': '', 'count': 0})
        },
        'bi_top_platforms': {
            'first': data['data'].get('团队平台Bug统计', {}).get('BI业务线', {}).get('top_platforms', {}).get('first', {'platform': '', 'count': 0}),
            'second': data['data'].get('团队平台Bug统计', {}).get('BI业务线', {}).get('top_platforms', {}).get('second', {'platform': '', 'count': 0})
        }
    }
    
    # 计算每个业务线的总质量
    for business_line in ['sfa_dev_quality', 'paas_dev_quality', 'deep_research_dev_quality', 'fcm_dev_quality', 'bi_dev_quality']:
        total = context[business_line]['total']
        if total['dev_count'] > 0:
            total['quality'] = round(total['bug_count'] / total['dev_count'], 2)
    
    # 渲染文档
    doc.render(context)
    
    # 如果没有指定输出路径，则使用默认路径
    if output_path is None:
        output_path = f'output/测试报告_{data["version"]}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.docx'
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 保存文档
    doc.save(output_path)
    return output_path

if __name__ == '__main__':
    try:
        # 从命令行参数获取版本号
        if len(sys.argv) < 2:
            print("请提供版本号参数")
            sys.exit(1)
            
        version = sys.argv[1]
        output_file = generate_report(version)
        print(f'报告生成成功！保存在: {output_file}')
    except Exception as e:
        print(f'生成报告时发生错误: {str(e)}') 