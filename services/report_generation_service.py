from typing import Dict, Any
from .data_analysis_service import DataAnalysisService
import json
import os
from datetime import datetime

class ReportGenerationService:
    """报告生成服务"""
    
    def __init__(self):
        self.data_analysis_service = DataAnalysisService()
        
    def generate_report(self, data: Dict[str, Any], version: str) -> Dict[str, Any]:
        """生成分析报告
        
        Args:
            data: 原始数据
            version: 版本号
            
        Returns:
            Dict[str, Any]: 分析报告
        """
        # 创建数据分析服务实例
        analysis_service = DataAnalysisService()
        
        # 创建TAPD API客户端实例
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from utils.tapd_api_client import TapdApiClient
        tapd_client = TapdApiClient(
            api_user=os.getenv("TAPD_API_USER", "fxiaoke"),
            api_password=os.getenv("TAPD_API_PASSWORD", "07ECB7C8-9492-C6E4-79FC-3D45AC634FXK")
        )
        
        # 计算测试周期
        test_cycle = analysis_service.calculate_test_cycle(data.get("object_tL7xk__c", {}))
        
        # 获取灰度发布期间的bug统计
        bugs_during_gray = analysis_service.analyze_bugs_during_gray_release(
            data.get("object_y31e4__c", {}),
            data.get("object_tL7xk__c", {})
        )
        
        # 获取团队功能特性统计
        team_features = analysis_service.analyze_team_features(data)
        
        # 获取按严重程度和状态统计的bug数量
        bugs_by_severity = analysis_service.analyze_bugs_by_severity_and_status(
            data.get("offline_bug__c", {})
        )
        
        # 获取按团队和平台统计的bug数量
        bugs_by_team = analysis_service.analyze_bugs_by_team_and_platform(
            data.get("offline_bug__c", {})
        )
        
        # 获取开发质量统计
        dev_quality = analysis_service.calculate_development_quality(
            data.get("offline_bug__c", {})
        )
        
        # 分析需求数量
        stories_count = analysis_service.analyze_stories_count(data, tapd_client)
        
        # 分析灰度期间bug数量
        gray_release_bugs = analysis_service.analyze_gray_release_bugs_count(data, tapd_client, version)
        
        # 生成报告
        report = {
            "version": version,
            "generate_time": datetime.now().isoformat(),
            "data": {
                "测试周期": {
                    "工作日": test_cycle["workdays"],
                    "开始时间": test_cycle["start_date"],
                    "结束时间": test_cycle["end_date"]
                },
                "需求统计": {
                    "总需求数": stories_count["total_count"]
                },
                "团队功能特性统计": team_features,
                "灰度发布期间Bug统计": bugs_during_gray,
                "Bug严重程度统计": bugs_by_severity,
                "团队平台Bug统计": bugs_by_team,
                "开发质量统计": dev_quality,
                "灰度期间bug数量": gray_release_bugs["total_count"]
            }
        }
        
        return report
        
    def save_report_to_file(self, report: Dict[str, Any], version: str) -> str:
        """将报告保存到文件
        
        Args:
            report: 报告数据
            version: 版本号
            
        Returns:
            str: 保存的文件路径
        """
        # 创建output目录（如果不存在）
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{version}_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        # 格式化报告数据
        formatted_report = {
            "version": version,
            "generate_time": datetime.now().isoformat(),
            "data": {
                "测试周期": report["data"]["测试周期"],
                "需求统计": report["data"]["需求统计"],
                "团队功能特性统计": report["data"]["团队功能特性统计"],
                #"灰度发布期间Bug统计": report["data"]["灰度发布期间Bug统计"],
                "Bug严重程度统计": report["data"]["Bug严重程度统计"],
                "团队平台Bug统计": report["data"]["团队平台Bug统计"],
                "开发质量统计": report["data"]["开发质量统计"],
                "灰度期间bug数量": report["data"]["灰度期间bug数量"]
            }
        }
        
        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(formatted_report, f, ensure_ascii=False, indent=2)
            
        return filepath
        
    def generate_and_save_report(self, data: Dict[str, Any], version: str) -> str:
        """生成并保存报告
        
        Args:
            data: 原始数据
            version: 版本号
            
        Returns:
            str: 保存的文件路径
        """
        report = self.generate_report(data, version)
        return self.save_report_to_file(report, version) 