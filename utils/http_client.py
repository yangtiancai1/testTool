import requests
import json
from typing import Dict, Any
from config import FXK_API_BASE_URL
from .api_response import ApiResponse

class HttpClient:
    @staticmethod
    def post(url: str, data: Dict[str, Any]) -> ApiResponse:
        headers = {
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
            'Connection': 'keep-alive'
        }
        try:
            response = requests.post(url, json=data, headers=headers)
            
            # 尝试解析响应内容
            try:
                response_data = response.json()
                return ApiResponse.from_dict(response_data)
            except json.JSONDecodeError as e:
                return ApiResponse(
                    code=-1,
                    message=f"响应解析失败: {str(e)}",
                    data={"raw_response": response.text}
                )
                
        except requests.exceptions.RequestException as e:
            return ApiResponse(
                code=-1,
                message=f"请求失败: {str(e)}",
                data={"error_type": type(e).__name__, "error_message": str(e)}
            ) 