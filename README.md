# 纷享销客API数据分析与报告生成工具

这是一个用于集成纷享销客API的Python工具，提供了数据获取、分析和报告生成功能。特别适用于版本测试数据分析和质量报告生成。

## 环境要求

- Python 3.9+
- Redis 6.0+
- FastAPI
- ngrok（用于远程访问）

## 项目结构

```
.
├── config.py                        # 配置文件
├── requirements.txt                 # 项目依赖
├── .env                             # 环境变量配置
├── .env.example                     # 环境变量配置示例
├── example.py                       # 基础使用示例
├── examples/                        # 详细示例目录
│   └── custom_object_data_example.py # 自定义对象数据获取示例
├── logs/                            # 日志目录
├── output/                          # 输出目录（报告和数据）
├── tests/                           # 测试目录
├── utils/                           # 工具类
│   ├── redis_client.py              # Redis客户端
│   ├── http_client.py               # HTTP请求客户端
│   ├── api_response.py              # API响应处理
│   └── fxk_api_client.py            # 纷享销客API客户端
└── services/                        # 业务服务
    ├── report_api.py                # 报告生成API服务
    ├── fxk_service.py               # 纷享销客服务
    ├── enterprise_auth_service.py   # 企业认证服务
    ├── custom_object_service.py     # 自定义对象服务
    ├── custom_object_data_service.py # 自定义对象数据服务
    ├── custom_object_data_filter_service.py # 数据过滤服务
    ├── data_analysis_service.py     # 数据分析服务
    ├── report_generation_service.py # 报告生成服务
    ├── fxk_wx_service.py            # 微信服务
    └── interfaces.py                # 接口定义
```

## 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows

# 安装依赖（使用清华镜像源加速）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 配置说明

1. 复制 `.env.example` 文件为 `.env`
2. 在 `.env` 文件中配置以下信息：
   - Redis配置（如果需要修改默认配置）
   - 纷享销客API配置（appId, appSecret, permanentCode, corpId）
   - 测试手机号（TEST_MOBILE）
   - 测试版本号（TEST_VERSION）

## API 服务

### 启动服务

```bash
# 启动报告生成服务
python services/report_api.py

# 服务默认运行在 http://localhost:8000
```

### 远程访问配置

使用 ngrok 实现远程访问：

```bash
# 安装 ngrok
brew install ngrok  # MacOS
# 或
snap install ngrok  # Linux

# 配置 ngrok authtoken（首次使用需要）
ngrok config add-authtoken 你的authtoken

# 启动 ngrok
ngrok http 8000
```

### API 端点

1. 生成报告
```bash
POST /generate-report
Content-Type: application/json

{
    "version": "9.5.0"
}
```

2. 查询报告状态
```bash
GET /report-status/{task_id}
```

3. 下载报告
```bash
GET /download-report/{task_id}
```

### 响应格式

1. 生成报告响应：
```json
{
    "status": "accepted",
    "message": "报告生成任务已接受",
    "task_id": "task_id的值"
}
```

2. 状态查询响应：
```json
{
    "status": "success|processing|error",
    "message": "状态描述",
    "report_path": "报告文件路径（仅在成功时返回）",
    "error": "错误信息（仅在失败时返回）"
}
```

## 主要功能

### 1. API数据获取
- 支持获取纷享销客自定义对象数据
- 支持复杂过滤条件和查询参数
- 自动管理CorpAccessToken
- Redis缓存支持（有效期7200秒）

### 2. 数据分析
- 支持测试周期计算
- Bug统计（按严重程度、状态、团队、平台）
- 开发质量分析
- 数据过滤和预处理

### 3. 报告生成
- 自动生成JSON格式报告
- 支持结构化数据输出
- 分析结果可视化（图表数据）
- 支持远程生成和下载

## 使用示例

### 基础API调用

```python
from services.fxk_service import FxkService

fxk_service = FxkService()
user_id = fxk_service.get_user_id_by_mobile("13800138000")
print(f"用户ID: {user_id}")
```

### 自定义对象数据获取与分析

```python
from services.custom_object_data_service import CustomObjectDataService
from services.custom_object_data_filter_service import CustomObjectDataFilterService
from services.report_generation_service import ReportGenerationService

# 初始化服务
mobile = "13800138000"
version = "9.4.5"
data_service = CustomObjectDataService(mobile=mobile)
filter_service = CustomObjectDataFilterService(version=version)
report_service = ReportGenerationService()

# 定义对象配置
object_config = {
    "object_api_name": "offline_bug__c",
    "fields": ["dev_team__c__r", "version__c", "severity__c", "status__c"],
    "filters": [
        {
            "field_name": "version__c",
            "field_values": [version],
            "operator": "EQ"
        }
    ],
    "limit": 100
}

# 获取数据
data = data_service.fetch_object_data(object_config["object_api_name"], 
                                     object_config["filters"],
                                     object_config.get("orders"), 
                                     object_config["limit"])

# 过滤数据
filtered_data = filter_service.filter_object_data({"offline_bug__c": data})

# 生成报告
report_file = report_service.generate_and_save_report(filtered_data, version)
print(f"报告已保存到: {report_file}")
```

### 远程调用示例

使用 curl：
```bash
# 生成报告
curl -X POST "https://你的ngrok地址/generate-report" \
     -H "Content-Type: application/json" \
     -d '{"version": "9.5.0"}'

# 查询状态
curl "https://你的ngrok地址/report-status/任务ID"

# 下载报告
curl -o report.docx "https://你的ngrok地址/download-report/任务ID"
```

## 完整示例

参见 `examples/custom_object_data_example.py` 文件，展示了如何：
1. 配置和初始化服务
2. 获取多个对象数据
3. 过滤和处理数据
4. 生成分析报告

## 运行示例

```bash
# 运行基础示例
python example.py

# 运行自定义对象数据示例
python examples/custom_object_data_example.py

# 启动 API 服务
python services/report_api.py
```

## 输出文件

运行示例后，会在 `output` 目录下生成两种文件：
1. 数据文件：`object_data_{version}_{timestamp}.json`
2. 报告文件：`report_{version}_{timestamp}.json`

## 日志

程序运行日志会保存在 `logs` 目录下：
- `custom_object_data_{timestamp}.log`
- `api_service_{timestamp}.log`

可以通过查看日志文件了解程序运行过程和调试可能的问题。

## 常见问题

1. 如果遇到依赖安装问题，可以尝试使用其他镜像源：
```bash
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

2. 如果 ngrok 无法连接，检查：
- 是否正确配置了 authtoken
- 本地服务是否正在运行
- 防火墙设置

3. 如果报告生成失败，检查：
- 日志文件中的错误信息
- 确保所需的模板文件存在
- 确保有足够的磁盘空间# sam
