from typing import Any, Dict, Optional

class ApiResponse:
    def __init__(self, code: int, message: str, data: Optional[Dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.data = data or {}

    @classmethod
    def from_dict(cls, response_dict: Dict[str, Any]) -> 'ApiResponse':
        # 检查是否是纷享销客的错误响应格式
        if 'errorCode' in response_dict:
            code = response_dict.get('errorCode', -1)
            message = response_dict.get('errorMessage', '未知错误')
            
            # 如果是成功响应，将所有字段作为数据
            if code == 0:
                data = {k: v for k, v in response_dict.items() if k not in ['errorCode', 'errorMessage']}
            else:
                data = {
                    'errorDescription': response_dict.get('errorDescription', ''),
                    'traceId': response_dict.get('traceId', '')
                }
            
            return cls(code=code, message=message, data=data)
        
        # 标准响应格式
        return cls(
            code=response_dict.get('code', -1),
            message=response_dict.get('message', '未知错误'),
            data=response_dict.get('data', {})
        )

    def is_success(self) -> bool:
        return self.code == 0

    def get_data(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def __str__(self) -> str:
        return f"ApiResponse(code={self.code}, message='{self.message}', data={self.data})" 