from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import subprocess
import sys
import os
import logging
from typing import Optional
import asyncio
from pathlib import Path
import json
import uuid
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="测试报告生成服务")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 存储报告生成状态
report_status = {}

class ReportRequest(BaseModel):
    version: str
    output_path: Optional[str] = None

class ReportStatus(BaseModel):
    status: str
    message: str
    report_path: Optional[str] = None
    error: Optional[str] = None

async def generate_report_task(version: str, task_id: str, output_path: Optional[str] = None):
    """异步生成报告的任务"""
    try:
        # 获取当前脚本所在目录
        current_dir = Path(__file__).parent.parent
        
        # 构建generate_report.py的完整路径
        report_script = current_dir / "generate_report.py"
        
        # 准备命令参数
        cmd = [sys.executable, str(report_script), version]
        
        # 如果提供了输出路径，添加到命令参数中
        if output_path:
            cmd.append(output_path)
        
        # 异步执行命令
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "未知错误"
            logger.error(f"生成报告失败: {error_msg}")
            report_status[task_id] = {
                "status": "error",
                "message": "生成报告失败",
                "error": error_msg
            }
            return
        
        # 解析输出以获取生成的报告路径
        output = stdout.decode()
        report_path = None
        for line in output.split('\n'):
            if '报告生成成功！保存在:' in line:
                report_path = line.split('保存在:')[1].strip()
                break
        
        if not report_path:
            report_status[task_id] = {
                "status": "error",
                "message": "无法确定生成的报告路径",
                "error": "报告生成成功但无法获取文件路径"
            }
            return
        
        report_status[task_id] = {
            "status": "success",
            "message": "报告生成成功",
            "report_path": report_path
        }
        
    except Exception as e:
        logger.error(f"生成报告时发生错误: {str(e)}")
        report_status[task_id] = {
            "status": "error",
            "message": "生成报告失败",
            "error": str(e)
        }

@app.post("/generate-report")
async def generate_report(request: ReportRequest, background_tasks: BackgroundTasks):
    """
    生成测试报告的API端点
    
    Args:
        request: 包含版本号和可选输出路径的请求体
        
    Returns:
        dict: 包含任务ID的响应
    """
    try:
        # 生成唯一任务ID
        task_id = str(uuid.uuid4())
        
        # 初始化任务状态
        report_status[task_id] = {
            "status": "processing",
            "message": "正在生成报告",
            "start_time": datetime.now().isoformat()
        }
        
        # 在后台启动报告生成任务
        background_tasks.add_task(
            generate_report_task,
            request.version,
            task_id,
            request.output_path
        )
        
        return {
            "status": "accepted",
            "message": "报告生成任务已接受",
            "task_id": task_id
        }
        
    except Exception as e:
        logger.error(f"接受报告生成任务时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/report-status/{task_id}")
async def get_report_status(task_id: str):
    """获取报告生成状态"""
    if task_id not in report_status:
        raise HTTPException(status_code=404, detail="任务ID不存在")
    
    return report_status[task_id]

@app.get("/download-report/{task_id}")
async def download_report(task_id: str):
    """下载生成的报告"""
    if task_id not in report_status:
        raise HTTPException(status_code=404, detail="任务ID不存在")
    
    status = report_status[task_id]
    if status["status"] != "success":
        raise HTTPException(status_code=400, detail="报告尚未生成完成")
    
    report_path = status["report_path"]
    if not report_path or not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="报告文件不存在")
    
    return FileResponse(
        report_path,
        filename=os.path.basename(report_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 