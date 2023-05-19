import asyncio
import sys

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app_env import auto_load_env
from app_logging import config_logging
from constant import BASE_PATH
from tools import reset_pid, JSONCache, process_tasks

auto_load_env()
config_logging()


async def run_tasks():
    cache = JSONCache(file= BASE_PATH / '__task__.json', init_content='[]')
    cache.reload()
    process_tasks(cache.data)


def master():
    reset_pid()
    if sys.argv[-1].strip() == 'stop':
        return

    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_tasks, 'interval', seconds=60)
    scheduler.start()

    loop = asyncio.get_event_loop()
    loop.run_forever()


if __name__ == '__main__':
    master()
