import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Redis配置
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# 纷享销客API配置
FXK_API_BASE_URL = 'https://open.fxiaoke.com/cgi'
FXK_APP_ID = os.getenv('FXK_APP_ID', '')
FXK_APP_SECRET = os.getenv('FXK_APP_SECRET', '')
FXK_PERMANENT_CODE = os.getenv('FXK_PERMANENT_CODE', '')

# OAuth2.0配置
FXK_OAUTH_REDIRECT_URL = os.getenv('FXK_OAUTH_REDIRECT_URL', '')
FXK_OAUTH_STATE_COOKIE_NAME = 'fxk_oauth_state'
FXK_OAUTH_ACCESS_TOKEN_COOKIE_NAME = 'fxk_oauth_access_token'
FXK_OAUTH_REFRESH_TOKEN_COOKIE_NAME = 'fxk_oauth_refresh_token'
FXK_OAUTH_OPEN_USER_ID_COOKIE_NAME = 'fxk_oauth_open_user_id'

# Token缓存配置
TOKEN_CACHE_KEY = 'fxk_corp_access_token'
TOKEN_EXPIRE_TIME = 7200  # 2小时
USER_ID_CACHE_KEY = 'fxk_user_id'  # 用户ID缓存键前缀 