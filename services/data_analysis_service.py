from typing import Dict, List, Any
from datetime import datetime, timedelta
import re
import os

class DataAnalysisService:
    """数据分析服务类"""
    
    @staticmethod
    def _extract_first_batch_date(schedule_text: str) -> datetime:
        """从发布计划文本中提取灰度真实企业第一批的日期
        
        Args:
            schedule_text: 发布计划文本
            
        Returns:
            datetime: 提取的日期，如果未找到则返回None
        """
        # 使用正则表达式匹配日期和批次信息
        pattern = r"(\d{4}\.\d{2}\.\d{2})日[夜]?\s*灰度真实企业第一批"
        match = re.search(pattern, schedule_text)
        if match:
            date_str = match.group(1)
            # 将日期字符串转换为datetime对象
            try:
                # 由于是夜间发布，我们取前一天作为实际开始日期
                date = datetime.strptime(date_str, "%Y.%m.%d")
                return date - timedelta(days=1)
            except ValueError:
                return None
        return None
    
    @staticmethod
    def _calculate_workdays(start_date: datetime, end_date: datetime) -> int:
        """计算两个日期之间的工作日数量（不包括周末）
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            int: 工作日数量
        """
        workdays = 0
        current_date = start_date
        
        while current_date <= end_date:
            # 0是周一，6是周日
            if current_date.weekday() < 5:  # 周一到周五
                workdays += 1
            current_date += timedelta(days=1)
            
        return workdays
    
    @staticmethod
    def calculate_test_cycle(data: Dict[str, Any]) -> Dict[str, Any]:
        """计算测试周期
        
        Args:
            data: object_tL7xk__c对象数据
            
        Returns:
            Dict[str, Any]: 测试周期信息，包含天数和具体时间
        """
        if not data or "dataList" not in data or not data["dataList"]:
            return {
                "days": 0,
                "workdays": 0,
                "start_date": None,
                "end_date": None
            }
            
        record = data["dataList"][0]  # 取最新一条记录
        try:
            # 从发布计划中提取灰度第一批时间
            schedule_text = record.get("field_eX1fb__c", "")
            first_batch_date = DataAnalysisService._extract_first_batch_date(schedule_text)
            
            if not first_batch_date:
                return {
                    "days": 0,
                    "workdays": 0,
                    "start_date": None,
                    "end_date": None
                }
                
            # 获取计划开始日期
            start_date = datetime.strptime(record["field_B79Io__c"], "%Y-%m-%d")
            
            # 计算总天数
            total_days = (first_batch_date - start_date).days
            
            # 计算工作日数量
            workdays = DataAnalysisService._calculate_workdays(start_date, first_batch_date)
            
            return {
                "days": total_days,
                "workdays": workdays,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": first_batch_date.strftime("%Y-%m-%d")
            }
            
        except (KeyError, ValueError) as e:
            return {
                "days": 0,
                "workdays": 0,
                "start_date": None,
                "end_date": None
            }
            
    @staticmethod
    def analyze_bugs_by_severity_and_status(data: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
        """根据严重程度和状态统计bug数量
        
        Args:
            data: offline_bug__c对象数据
            
        Returns:
            Dict[str, Dict[str, int]]: 统计结果
        """
        if not data or "dataList" not in data:
            return {}
            
        # 严重程度映射
        severity_map = {
            "fatal": "致命",
            "serious": "严重",
            "normal": "一般",
            "advice": "建议"
        }
        
        result = {
            "致命": {"新": 0, "已解决": 0, "已关闭": 0, "total": 0},
            "严重": {"新": 0, "已解决": 0, "已关闭": 0, "total": 0},
            "一般": {"新": 0, "已解决": 0, "已关闭": 0, "total": 0},
            "建议": {"新": 0, "已解决": 0, "已关闭": 0, "total": 0},
            "total": 0
        }
        
        for bug in data["dataList"]:
            team = bug.get("dev_team__c__r", "")
            platform = bug.get("platform__c", "")
            
            # 过滤掉所属团队或平台为空的数据
            if not team or team == "null" or team == "未分类" or not platform:
                continue
                
            severity = bug.get("severity__c", "")
            status = bug.get("status__c", "")
            
            # 获取中文严重程度
            severity_cn = severity_map.get(severity, "")
            if not severity_cn:
                continue
                
            if severity_cn in result and status in result[severity_cn]:
                result[severity_cn][status] += 1
                result[severity_cn]["total"] += 1
                result["total"] += 1
                
        return result
        
    @staticmethod
    def analyze_bugs_by_team_and_platform(data: Dict[str, Any]) -> Dict[str, Dict[str, Dict[str, Dict[str, Dict[str, int]]]]]:
        """按团队和平台统计不同严重程度和状态的bug数量
        
        Args:
            data: offline_bug__c对象数据
            
        Returns:
            Dict[str, Dict[str, Dict[str, Dict[str, Dict[str, int]]]]]: 统计结果，包含团队统计和业务线统计
        """
        if not data or "dataList" not in data:
            return {}
            
        result = {}
        team_total = {}  # 用于统计每个团队的总bug数
        business_line_total = {}  # 用于统计每个业务线的总bug数
        platform_total = {}  # 用于统计每个业务线各平台的bug数
        
        # 定义需要保留的业务线和团队
        business_line_teams = {
            "SFA业务线": ["售中团队", "售前团队"],
            "PAAS平台": ["流程团队", "基础业务团队", "协同业务团队", "元数据权限组"],
            "深研业务线": ["制造行业组", "订货业务组"],
            "快消业务线": ["快消团队"],  # 快消团队作为独立业务线
            "BI业务线":["BI团队"]
        }
        
        # 初始化业务线统计
        for business_line in business_line_teams:
            result[business_line] = {}
            business_line_total[business_line] = 0
            platform_total[business_line] = {}
        
        for bug in data["dataList"]:
            team = bug.get("dev_team__c__r", "")
            platform = bug.get("platform__c", "")
            
            # 过滤掉所属团队或平台为空的数据
            if not team or team == "null" or team == "未分类" or not platform:
                continue
                
            severity = bug.get("severity__c", "")
            status = bug.get("status__c", "")
            
            # 业务线统计
            for business_line, teams in business_line_teams.items():
                if team in teams:
                    if platform not in result[business_line]:
                        result[business_line][platform] = {
                            "fatal": {"新": 0, "已解决": 0, "已关闭": 0},
                            "serious": {"新": 0, "已解决": 0, "已关闭": 0},
                            "normal": {"新": 0, "已解决": 0, "已关闭": 0},
                            "advice": {"新": 0, "已解决": 0, "已关闭": 0}
                        }
                        platform_total[business_line][platform] = 0
                        
                    if severity in result[business_line][platform] and status in result[business_line][platform][severity]:
                        result[business_line][platform][severity][status] += 1
                        business_line_total[business_line] += 1
                        platform_total[business_line][platform] += 1
        
        # 为每个业务线添加平台bug小计和排序信息
        for business_line in result:
            # 计算每个平台的bug总数
            for platform in result[business_line]:
                if platform != "total":
                    total = 0
                    for severity in ["fatal", "serious", "normal", "advice"]:
                        for status in ["新", "已解决", "已关闭"]:
                            total += result[business_line][platform][severity][status]
                    result[business_line][platform]["total"] = total
            
            # 对平台按bug数排序
            sorted_platforms = sorted(
                [(p, result[business_line][p]["total"]) for p in result[business_line] if p != "total"],
                key=lambda x: x[1],
                reverse=True
            )
            
            # 添加bug数最多的两个平台信息
            if len(sorted_platforms) >= 2:
                result[business_line]["top_platforms"] = {
                    "first": {
                        "platform": sorted_platforms[0][0],
                        "count": sorted_platforms[0][1]
                    },
                    "second": {
                        "platform": sorted_platforms[1][0],
                        "count": sorted_platforms[1][1]
                    }
                }
            elif len(sorted_platforms) == 1:
                result[business_line]["top_platforms"] = {
                    "first": {
                        "platform": sorted_platforms[0][0],
                        "count": sorted_platforms[0][1]
                    }
                }
            
            # 添加业务线总bug数
            result[business_line]["total"] = business_line_total[business_line]
        
        return result
        
    @staticmethod
    def calculate_development_quality(data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """计算开发质量
        
        Args:
            data: offline_bug__c对象数据
            
        Returns:
            Dict[str, Dict[str, float]]: 开发质量统计结果，包含每个业务线开发质量最高的平台信息
        """
        if not data or "dataList" not in data:
            return {}
            
        # 定义需要保留的业务线和团队
        business_line_teams = {
            "SFA业务线": ["售中团队", "售前团队"],
            "PAAS平台": ["流程团队", "基础业务团队", "协同业务团队", "元数据权限组"],
            "深研业务线": ["互联平台组", "制造行业组", "订货业务组"],
            "快消团队": ["快消团队"],
            "BI业务线":["BI团队"]
        }
        
        # 统计每个业务线每个平台的开发人数和缺陷数
        business_line_stats = {}
        
        for bug in data["dataList"]:
            team = bug.get("dev_team__c__r", "")
            # 过滤掉所属团队为空的数据
            if not team or team == "null" or team == "未分类":
                continue
                
            platform = bug.get("platform__c", "")
            # 过滤掉平台为空的数据
            if not platform:
                continue
                
            fixer = bug.get("fixer__c", [])
            
            # 确定业务线
            business_line = None
            for bl, teams in business_line_teams.items():
                if team in teams:
                    business_line = bl
                    break
            
            if not business_line:
                continue
                
            if business_line not in business_line_stats:
                business_line_stats[business_line] = {}
            if platform not in business_line_stats[business_line]:
                business_line_stats[business_line][platform] = {
                    "bug_count": 0,
                    "dev_count": set()
                }
                
            business_line_stats[business_line][platform]["bug_count"] += 1
            if fixer and isinstance(fixer, list):
                business_line_stats[business_line][platform]["dev_count"].update(fixer)
                
        # 计算开发质量并格式化输出
        dev_quality_stats = {}
        for business_line, platforms in business_line_stats.items():
            dev_quality_stats[business_line] = {}
            max_quality = 0
            max_quality_platform = None
            
            for platform, stats in platforms.items():
                bug_count = stats["bug_count"]
                dev_count = len(stats["dev_count"])
                quality = round(bug_count / dev_count, 2) if dev_count > 0 else 0
                
                dev_quality_stats[business_line][platform] = {
                    "bug_count": bug_count,
                    "dev_count": dev_count,
                    "quality": quality
                }
                
                # 记录开发质量最高的平台
                if quality > max_quality:
                    max_quality = quality
                    max_quality_platform = platform
            
            # 添加开发质量最高的平台信息
            if max_quality_platform:
                dev_quality_stats[business_line]["best_platform"] = {
                    "platform": max_quality_platform,
                    "quality": max_quality,
                    "bug_count": dev_quality_stats[business_line][max_quality_platform]["bug_count"],
                    "dev_count": dev_quality_stats[business_line][max_quality_platform]["dev_count"]
                }
        
        return dev_quality_stats

    @staticmethod
    def analyze_bugs_during_gray_release(data, release_plan):
        """分析灰度期间的bug数据
        
        Args:
            data: object_y31e4__c对象数据
            release_plan: object_tL7xk__c对象数据
            
        Returns:
            dict: 包含灰度期间的bug统计信息
        """
        if not data or not release_plan:
            return {
                "gray_release_period": {
                    "start": None,
                    "end": None
                },
                "bug_count": 0
            }
        
        # 从发布计划中提取灰度开始时间和全网发布时间
        if "dataList" not in release_plan or not release_plan["dataList"]:
            return {
                "gray_release_period": {
                    "start": None,
                    "end": None
                },
                "bug_count": 0
            }
            
        schedule_text = release_plan["dataList"][0].get("field_eX1fb__c", "")
        if not schedule_text:
            return {
                "gray_release_period": {
                    "start": None,
                    "end": None
                },
                "bug_count": 0
            }
        
        # 将文本按行分割并清理每行的空白字符
        lines = [line.strip() for line in schedule_text.split('\n')]
        
        # 解析灰度开始时间（第一次灰度发布时间）
        gray_start = None
        for line in lines:
            gray_start_match = re.search(r"(\d{4}\.\d{2}\.\d{2})日[夜晚]?\s*灰度", line)
            if gray_start_match:
                gray_start_str = gray_start_match.group(1)
                gray_start = datetime.strptime(gray_start_str, "%Y.%m.%d")
                break
        
        if not gray_start:
            return {
                "gray_release_period": {
                    "start": None,
                    "end": None
                },
                "bug_count": 0
            }
        
        # 解析全网发布时间
        full_release = None
        for line in lines:
            full_release_match = re.search(r"(\d{4}\.\d{2}\.\d{2})日\s*(?:24:00)?\s*全网发布", line)
            if full_release_match:
                full_release_str = full_release_match.group(1)
                full_release = datetime.strptime(full_release_str, "%Y.%m.%d")
                break
        
        if not full_release:
            return {
                "gray_release_period": {
                    "start": None,
                    "end": None
                },
                "bug_count": 0
            }
        
        # 统计在灰度期间创建的bug数量
        bug_count = 0
        if "dataList" in data:
            for bug in data["dataList"]:
                create_time = bug.get("create_time")
                if not create_time:
                    continue
                    
                # 将时间戳转换为datetime对象
                try:
                    create_time = datetime.fromtimestamp(create_time / 1000)  # 假设时间戳是毫秒级的
                except (TypeError, ValueError):
                    continue
                    
                # 检查bug是否在灰度期间创建
                if gray_start <= create_time <= full_release:
                    bug_count += 1
        
        # return {
        #     "gray_release_period": {
        #         "start": gray_start.strftime("%Y-%m-%d"),
        #         "end": full_release.strftime("%Y-%m-%d")
        #     },
        #     "bug_count": bug_count
        # }

    def analyze_team_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析不同团队的功能特性
        
        Args:
            data: 过滤后的数据
            
        Returns:
            Dict[str, Any]: 团队功能特性统计结果
        """
        if not data:
            print("数据为空")
            return {}
            
        # 获取业务模块和功能清单数据
        business_modules = data.get("object_xkBG2__c", {}).get("dataList", [])
        features = data.get("object_notes__c", {}).get("dataList", [])
        
        print(f"业务模块数量: {len(business_modules)}")
        print(f"功能清单数量: {len(features)}")
        
        # 创建业务模块名称到团队的映射
        module_to_team = {}
        for module in business_modules:
            if isinstance(module, dict):
                module_name = module.get("display_name")
                team = module.get("field_Xig8k__c")
                if module_name and team:
                    module_to_team[module_name] = team
                    print(f"模块 {module_name} 属于团队 {team}")
        
        print(f"模块到团队的映射数量: {len(module_to_team)}")
        
        # 按团队和应用统计功能特性
        team_features = {}
        for feature in features:
            if not isinstance(feature, dict):
                print(f"功能数据不是字典类型: {feature}")
                continue
                
            # 获取模块引用，可能是字典或字符串
            module_ref = feature.get("field_2rMd8__c__r", {})
            module_name = None
            
            if isinstance(module_ref, dict):
                module_name = module_ref.get("display_name")
            elif isinstance(module_ref, str):
                module_name = module_ref
                
            print(f"处理功能: {feature.get('display_name')}, 所属模块: {module_name}")
            
            if not module_name:
                print("模块名称为空")
                continue
                
            if module_name not in module_to_team:
                print(f"未找到模块 {module_name} 对应的团队")
                continue
                
            team = module_to_team[module_name]
            app = feature.get("field_s1Ovl__c")
            
            if not app:
                continue
                
            # 使用"应用-团队"作为key
            key = f"{app}-{team}"
            
            if key not in team_features:
                team_features[key] = {
                    "features": []
                }
                
            # 添加功能描述
            feature_desc = feature.get("display_name")
            if feature_desc:
                team_features[key]["features"].append(feature_desc)
                print(f"添加功能 {feature_desc} 到 {key}")
        
        print(f"最终统计结果: {team_features}")
        return team_features

    def analyze_stories_count(self, data: Dict[str, Any], tapd_client: Any) -> Dict[str, Any]:
        """分析需求数量
        
        Args:
            data: 原始数据
            tapd_client: TAPD API客户端实例
            
        Returns:
            Dict[str, Any]: 需求数量统计结果
        """
        print("开始分析需求数量...")
        stories_count = 0
        
        # 获取object_0yrBp__c对象的数据
        object_data = data.get("object_0yrBp__c", {})
        data_list = object_data.get("dataList", [])
        print(f"获取到 {len(data_list)} 条团队数据")
        
        # 遍历每个团队的数据
        for item in data_list:
            workspace_id = item.get("field_W6W5T__c")
            iteration_id = item.get("field_msrO4__c")
            team_ref = item.get("field_3ugLn__c__r", {})
            team_name = team_ref.get("display_name", "未知团队") if isinstance(team_ref, dict) else "未知团队"
            
            print(f"处理团队: {team_name}, workspace_id: {workspace_id}, iteration_id: {iteration_id}")
            
            if workspace_id and iteration_id:
                try:
                    # 调用TAPD API获取需求数量
                    count = tapd_client.get_stories_count(
                        workspace_id=int(workspace_id),
                        iteration_id=int(iteration_id)
                    )
                    
                    if count is not None:
                        stories_count += count
                        print(f"团队 {team_name} 的需求数量: {count}")
                except Exception as e:
                    print(f"获取团队 {team_name} 的需求数量失败: {str(e)}")
            else:
                print(f"团队 {team_name} 缺少workspace_id或iteration_id")
        
        print(f"需求数量统计完成，总需求数: {stories_count}")
        
        return {
            "total_count": stories_count
        }

    def analyze_gray_release_bugs_count(self, data: Dict[str, Any], tapd_client: Any, version: str) -> Dict[str, Any]:
        """分析灰度期间的bug数量
        
        Args:
            data: 原始数据
            tapd_client: TAPD API客户端实例
            version: 版本号
            
        Returns:
            Dict[str, Any]: 灰度期间bug数量统计结果
        """
        print("开始分析灰度期间bug数量...")
        
        print(f"获取到的版本号: {version}")
            
        # 拼接标题
        title = f"{version.replace('.', '')}内测"
        print(f"拼接的标题: {title}")
            
        try:
            # 直接调用TAPD API获取bug数量，使用固定的workspace_id
            print(f"调用TAPD API获取bug数量，参数: workspace_id=20019471, title={title}, version_report=内测")
            
            count = tapd_client.get_bugs_count(
                workspace_id=20019471,
                title=title,
                version_report="内测"
            )
            
            print(f"TAPD API返回结果: {count}")
            
            return {
                "total_count": count if count is not None else 0,
            }
            
        except Exception as e:
            print(f"获取灰度期间bug数量失败: {str(e)}")
            return {
                "total_count": 0,
            }