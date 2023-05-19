"""获取环境变量"""
import os
from dotenv import load_dotenv
from constant import BASE_PATH

MODE_MAP = {
    'dev': 'development',
    'prod': 'production',
}


def auto_load_env():
    """加载项目根目录下的.env文件"""
    load_dotenv(BASE_PATH / '.env', override=False)
    app_run_mode = os.environ.setdefault('APP_RUN_MODE', 'dev')
    load_dotenv(BASE_PATH / f".env.{MODE_MAP.get(app_run_mode, 'development')}", override=True)


def _normalize(value=None):
    """规范化.env文件的值"""
    value = '' if value is None else value
    if len(value) in (4, 5) and value.lower() in ('true', 'false'):
        return value.lower() == 'true'

    elif value.isdigit():
        return int(value)

    return value


def get_env(params=None, prefix=''):
    """加强获取环境变量"""
    if isinstance(params, str):
        return _normalize(os.getenv(f"{prefix}_{params}" if prefix else params))

    prefix = prefix + '_' if prefix else ''
    keys = params if params else [_ for _ in os.environ.keys() if _.startswith(prefix)]

    return {
        (k.replace(prefix, '')).lower(): _normalize(os.getenv((prefix + k) if params else k))
        for k in keys
    }
