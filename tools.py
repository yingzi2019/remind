import os
import json
import asyncio
import logging
import random
import threading
import time
from datetime import datetime, timedelta
from importlib import import_module
from pathlib import Path
from typing import Union

import addict
import psutil
from notifypy import Notify

from app_env import auto_load_env
from constant import BASE_PATH

logger = logging.getLogger("default")
platform_notifier = Notify(default_notification_application_name="Remind")
message_type = {"info": 0, "success": 64, "error": 16, "warning": 48}


def wait_next_minute():
    target_time = (datetime.now() + timedelta(minutes=1)).replace(
        microsecond=0, second=0
    )
    while True:
        now = datetime.now()
        if now >= target_time:
            logger.info(f"checked: {now.strftime('%Y-%m-%d %H:%M:%S.%f')}")
            break
        time.sleep(0.005)


def set_timeout(delay, cb, *args):
    """异步调用函数，并增加异常处理"""
    def wrapper(*args):
        try:
            cb(*args)
        except Exception as e:
            logger.error(f"Exception set_timeout: {e}")

    threading.Timer(delay, wrapper, args).start()

def terminate_process_by_pid(pid):
    try:
        process = psutil.Process(pid)
        process.terminate()
        process.wait()
        logger.info(f"Terminated process with PID: {pid}")
        return True
    except Exception:
        logger.info(f"PID {pid} is invalid.")
        return False


def reset_pid():
    conf = JSONCache(file=BASE_PATH / "__conf__.json")
    old_pid = conf.pid
    terminate_process_by_pid(old_pid)
    conf["pid"] = os.getpid()

    logger.info(f"终止PID: {old_pid}, 新的PID: {conf.pid}")


def parser_cron_item(chars):
    """
    Get a range and return a list
    :param chars:
    :return: list
    """
    if "/" in chars:
        s, f = chars.split("/")
        return [
            value for idx, value in enumerate(parser_cron_item(s)) if idx % int(f) == 0
        ]
    elif "-" in chars:
        begin, end = chars.split("-")
        return [i for i in range(int(begin), int(end) + 1)]
    elif "," in chars:
        return [int(i) for i in chars.split(",")]
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
    m, h, d, mon, w = time.strftime("%M %H %d %m %w").split()

    try:
        c_m, c_h, c_d, c_mon, c_w = crontab.split()

        b_m = True if c_m == "*" else int(m) in parser_cron_item(c_m)
        b_h = True if c_h == "*" else int(h) in parser_cron_item(c_h)
        b_d = True if c_d == "*" else int(d) in parser_cron_item(c_d)
        b_mon = True if c_mon == "*" else int(mon) in parser_cron_item(c_mon)
        b_w = True if c_w == "*" else int(w) in parser_cron_item(c_w)
        return b_m and b_h and b_d and b_mon and b_w
    except Exception as e:
        logger.error(f"cron({crontab}) 解析错误: {e}")
        return False


class JSONCache:
    """
    一个用于管理 JSON 数据的类，支持使用 addict 的 Dict 进行字典操作，且兼容数组操作。
    用法：
        with JSONCache("cache_file.json") as cache:
            cache['key'] = 'value'  # 字典操作
            cache[0] = 'value'      # 数组操作
    """

    def __init__(self, file="_temp_.json", init_content="{}"):
        self.file = Path(file).with_suffix(".json")
        if not self.file.exists():
            self.file.parent.mkdir(parents=True, exist_ok=True)
            self.__save(init_content)
        self._reload()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__save()

    def __read_file(self):
        """从文件中读取 JSON 内容。"""
        with self.file.open("r", encoding="utf-8") as f:
            return json.load(f)

    def __save(self, content=None):
        """保存数据到文件。如果提供了内容，则写入初始内容。"""
        with self.file.open("w", encoding="utf-8") as f:
            if content is not None:
                f.write(content)
            else:
                json.dump(self.data, f, ensure_ascii=False, indent=4)

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value
        self.__save()

    def __delitem__(self, key):
        del self.data[key]
        self.__save()

    def __getattr__(self, key):
        if isinstance(self.data, dict):
            return self.data.get(key)
        elif isinstance(self.data, list):
            try:
                index = int(key)  # 尝试将 key 转换为整数
                if 0 <= index < len(self.data):
                    return self.data[index]
            except ValueError:
                pass
        raise AttributeError(f"'JSONCache' object has no attribute '{key}'")

    def _reload(self):
        """从文件重新加载数据。"""
        data = self.__read_file()
        if isinstance(data, dict):
            self.data = addict.Dict(data)
        else:
            self.data = [addict.Dict(item) for item in data]

    def _setdefault(self, key, default):
        """如果键不存在，则设置默认值。"""
        if isinstance(self.data, dict):
            if key not in self.data:
                self.data[key] = default
                self.__save()
            return self.data[key]
        else:
            raise TypeError("Only dict type supports '_setdefault'.")


def show_normal_message(message: Union[str, dict]):
    """在windows中显示消息"""
    if isinstance(message, str):
        message = {"content": message}
    elif not isinstance(message, dict):
        raise ValueError("message is should be a dictionary or a string.")

    logger.info("task: " + json.dumps(message, indent=2, ensure_ascii=False))
    platform_notifier.title = message.get("title", message.get("type", "info"))
    platform_notifier.message = message.get("content", "")
    platform_notifier.send()


def process_tasks(tasks):
    for task in tasks:
        if "func" in task:
            if task["func"] == "skip":
                continue
            elif task["func"] == "reload_environment":
                auto_load_env()
                continue
            elif task["func"] == "reload_addons":
                add_addons()
                continue
            elif task["func"] == "stop":
                time.sleep(20)
                asyncio.get_event_loop_policy().get_event_loop().stop()
                return logger.info(f"tasks is stop.")

        if "cron" in task:
            if cron(task["cron"]):
                try:
                    func = funcs.get(task.get("func"))
                    if not func or not callable(func):
                        return logger.error(f"{func} is not callable. skip the {task}.")
                    task = func(task)
                    set_timeout(0, show_normal_message, task)
                except Exception as e:
                    error_message = f"task run time error : {e}"
                    logger.error(error_message)
                    show_normal_message(
                        {
                            "type": "error",
                            "title": "定时任务运行出错",
                            "message": error_message,
                        }
                    )
        else:
            logger.error(f"无效的task: ｛task｝")
            continue


def phrase(task):
    """从文件中选取一行疆内容替换显示"""
    filename = "phrase.txt"
    if "filename" in task:
        filename = task["filename"]
    file_ins = BASE_PATH / filename
    data = file_ins.open("rt", encoding="utf-8").readlines()
    task["content"] = task["content"] + random.choice(
        [i.strip() for i in data if i.strip()]
    )
    return task


def add_addons():
    """收集addons中的函数"""
    for item in BASE_PATH.joinpath("addons").glob("*.py"):
        module_path = item.relative_to(BASE_PATH).as_posix().replace("/", ".")[:-3]
        module = import_module(module_path)
        if hasattr(module, "__all__"):
            for _item in module.__all__:
                funcs[_item] = getattr(module, _item)


funcs = {
    "normal": lambda x: x,
    "phrase": phrase,
}

add_addons()
