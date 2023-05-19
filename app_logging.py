"""
配置日志文件
"""
import logging
from logging.config import dictConfig

from constant import BASE_PATH
from app_env import auto_load_env, get_env


class Formatter(logging.Formatter):
    def format(self, record):
        record.level = record.levelname.center(10)
        record.name = record.name.center(12)
        return super().format(record)


def config_logging():
    debug = get_env('APP_DEBUG')
    handlers = ['default']
    level = 'DEBUG' if debug else 'INFO'
    log_file = BASE_PATH.joinpath('dev_logs' if debug else 'logs', 'Runtime.log')
    debug and handlers.append('console')
    log_file.parent.mkdir(parents=True, exist_ok=True)

    return dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                '()': Formatter,
                'format': '[%(asctime)s] [%(level)s] [%(name)s] [%(pathname)s: %(lineno)d] [%(funcName)s] %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'handlers': {
            'console': {
                'level': level,
                'class': 'logging.StreamHandler',
                'formatter': 'verbose'
            },
            'default': {
                'level': level,
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': log_file,
                'when': 'W3',
                'interval': 1,
                # 'maxBytes': 1024 * 1024 * 25,
                'backupCount': 7,  # 最多备份几个
                'formatter': 'verbose',
                'encoding': 'utf-8',
            }
        },
        'loggers': {
            'default': {
                'handlers': handlers,
                'level': 'DEBUG'
            },
            'spider': {
                'handlers': handlers,
                'level': 'DEBUG'
            },
            'web': {
                'handlers': handlers,
                'level': 'DEBUG'
            },
        },
    })


if __name__ == '__main__':
    auto_load_env()  # 加载环境变量
    config_logging()  # 配置logging

    # 测试
    logger = logging.getLogger('default')
    logger.debug('----- debug')
    logger.info('----- info')
