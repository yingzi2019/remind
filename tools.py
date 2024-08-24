import asyncio
import os
import random
import sys
import time
import json
import logging
from datetime import datetime, timedelta

import win32api
import threading
from pathlib import Path
from typing import Union
from pydantic import BaseModel

from app_env import auto_load_env
from constant import BASE_PATH
from importlib import import_module

logger = logging.getLogger('default')
message_type = {
    'info': 0,
    'success': 64,
    'error': 16,
    'warning': 48
}


def is_pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def wait_next_minute():
    target_time = (datetime.now() + timedelta(minutes=1)).replace(microsecond=0, second=0)
    while True:
        now = datetime.now()
        if now >= target_time:
            print('checked: ', now)
            break
        time.sleep(0.005)

def set_timeout(delay, cb, *args):
    """异步调用函数"""
    threading.Timer(delay, cb, args).start()


def reset_pid():
    conf = JSONCache(file=BASE_PATH / '__conf__.json')
    command = 'kill -9 %s' % conf.pid if sys.platform == 'linux' else 'cmd /c taskkill /f /pid %s' % conf.pid
    if is_pid_alive(conf['pid']):
        os.system(command)

    conf['pid'] = os.getpid()

    logger.info(f'终止PID: {command}, 新的PID: {conf.pid}')


def parser_cron_item(chars):
    """
    Get a range and return a list
    :param chars:
    :return: list
    """
    if '/' in chars:
        s, f = chars.split('/')
        return [value for idx, value in enumerate(parser_cron_item(s)) if idx % int(f) == 0]
    elif '-' in chars:
        begin, end = chars.split('-')
        return [i for i in range(int(begin), int(end) + 1)]
    elif ',' in chars:
        return [int(i) for i in chars.split(',')]
    else:
        return [int(chars)]


def cron(crontab: str):
    """
    Determine whether crontab matches the current time
    :param crontab: Minute Hour Day Month Week
    :return: bool
    Minute [00 - 59]
    Hour [00 - 23]
    Day of Month [01 - 31]
    Month [01 - 12]
    Week [0 - 6] -> [日 - 六]
    *: All possible values
    /: frequency of range
    -: range
    ,: List range
    """
    m, h, d, mon, w = time.strftime('%M %H %d %m %w').split()

    try:
        c_m, c_h, c_d, c_mon, c_w = crontab.split()

        b_m = True if c_m == '*' else int(m) in parser_cron_item(c_m)
        b_h = True if c_h == '*' else int(h) in parser_cron_item(c_h)
        b_d = True if c_d == '*' else int(d) in parser_cron_item(c_d)
        b_mon = True if c_mon == '*' else int(mon) in parser_cron_item(c_mon)
        b_w = True if c_w == '*' else int(w) in parser_cron_item(c_w)
        return b_m and b_h and b_d and b_mon and b_w
    except Exception as e:
        logger.error(f'cron({crontab}) 解析错误: {e}')
        return False


class JSONCache(object):
    """
    cache = JSONCache()
    cache.setdefault('work time', '996')
    """

    def __init__(self, file='_temp_.json', init_content='{}'):
        if isinstance(file, str):
            if not file.endswith('.json'):
                file += '.json'

        file = file if isinstance(file, Path) else Path(file)
        if not file.exists():
            file.parent.mkdir(exist_ok=True)
            file.write_text(init_content)

        self.data = json.load(file.open('rt', encoding='utf-8') or init_content)
        self.file = file

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__save()

    def __save(self):
        json.dump(self.data, self.file.open('wt'), ensure_ascii=False)

    def __getattr__(self, key):
        if isinstance(self.data, dict):
            return self.data[key] if key in self.data else None
        return None

    def __getitem__(self, key):
        ret = self.data[key]
        return ret

    def __setitem__(self, key, value):
        self.data[key] = value
        self.__save()

    def __delitem__(self, key):
        del self.data[key]
        self.__save()

    def reload(self):
        self.data = json.load(self.file.open('rt', encoding='utf-8'))


class Message(BaseModel):
    type: str = 'info'
    title: str = ''
    content: str = 'testing'


def show_windows_message(message: Union[str, dict]):
    """在windows中显示消息"""
    if isinstance(message, str):
        message = {'content': message}
    elif not isinstance(message, dict):
        raise ValueError('message is should be a dictionary or a string.')

    logger.info('task: ' + json.dumps(message, indent=2, ensure_ascii=False))

    message = Message(**message)

    return win32api.MessageBoxEx(0, message.content, message.title, message_type[message.type])


def process_tasks(tasks):
    for task in tasks:
        if 'func' in task:
            if task['func'] == 'skip':
                continue
            elif task['func'] == 'reload_environment':
                auto_load_env()
                continue
            elif task['func'] == 'reload_addons':
                add_addons()
                continue
            elif task['func'] == 'stop':
                time.sleep(20)
                asyncio.get_event_loop_policy().get_event_loop().stop()
                return logger.info(f'tasks is stop.')

        if 'cron' in task:
            if cron(task['cron']):
                try:
                    func = funcs.get(task.get('func'))
                    if not func or not callable(func):
                        return logger.error(f'{func} is not callable. skip the {task}.')
                    task = func(task)
                    set_timeout(0, show_windows_message, task)
                    # show_windows_message(task)
                except Exception as e:
                    error_message = f"task run time error : {e}"
                    logger.error(error_message)
                    show_windows_message({
                        "type": "error",
                        "title": "定时任务运行出错",
                        "message": error_message
                    })
        else:
            logger.error(f'无效的task: ｛task｝')
            continue


def phrase(task):
    """从文件中选取一行疆内容替换显示"""
    filename = 'phrase.txt'
    if 'filename' in task:
        filename = task['filename']
    file_ins = BASE_PATH / filename
    data = file_ins.open('rt', encoding='utf-8').readlines()
    task['content'] = task['content'] + random.choice([
        i.strip() for i in data if i.strip()
    ])
    return task


def add_addons():
    """收集addons中的函数"""
    for item in BASE_PATH.joinpath('addons').glob('*.py'):
        module_path = item.relative_to(BASE_PATH).as_posix().replace('/', '.')[:-3]
        module = import_module(module_path)
        if hasattr(module, '__all__'):
            for _item in module.__all__:
                funcs[_item] = getattr(module, _item)


funcs = {
    'normal': lambda x: x,
    'phrase': phrase,
}

add_addons()
