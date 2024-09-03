"""获取环境变量"""
import os
from dotenv import load_dotenv
from constant import BASE_PATH

MODE_MAP = {
    "dev": "development",
    "prod": "production",
}


def auto_load_env():
    """加载项目根目录下的 .env 文件，并根据 APP_RUN_MODE 加载相应的环境文件"""
    try:
        load_dotenv(BASE_PATH / ".env", override=False)
    except Exception as e:
        print(f"Error loading .env file: {e}")

    app_run_mode = os.environ.setdefault("APP_RUN_MODE", "dev")
    env_file = BASE_PATH / f".env.{MODE_MAP.get(app_run_mode, 'development')}"

    try:
        load_dotenv(env_file, override=True)
    except Exception as e:
        print(f"Error loading environment-specific .env file ({env_file}): {e}")


def _normalize(value=None):
    """规范化 .env 文件的值"""
    if value is None:
        return ""

    value = str(value).strip().lower()

    if value in ("true", "false"):
        return value == "true"

    if value.isdigit():
        return int(value)

    try:
        return float(value)
    except ValueError:
        return value


def get_env(params=None, prefix=""):
    """获取环境变量，支持前缀和参数"""
    if isinstance(params, str):
        return _normalize(os.getenv(f"{prefix}_{params}" if prefix else params))

    prefix = f"{prefix}_" if prefix else ""
    keys = (
        params
        if isinstance(params, list)
        else [k for k in os.environ.keys() if k.startswith(prefix)]
    )

    return {(k[len(prefix) :]).lower(): _normalize(os.getenv(k)) for k in keys}
