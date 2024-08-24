import logging
from playwright.sync_api import Playwright, sync_playwright
from app_env import get_env
from tools import set_timeout, cron

logger = logging.getLogger('default')


def login_email_and_logout(task):
    """自动登录邮箱, 用于激活."""

    def action():
        with sync_playwright() as playwright:
            email_config = get_env(prefix='EMAIL')

            logger.info(f'start')
            browser = playwright.chromium.launch(headless=not get_env('APP_RUN_DEBUG'), slow_mo=1500)
            context = browser.new_context()
            page = context.new_page()
            page.goto("https://app.tuta.com/login", wait_until='networkidle', timeout=90000)
            page.get_by_label("电子邮件地址").click()
            page.get_by_label("电子邮件地址").type(email_config['user'], delay=.3)
            page.get_by_label("密码", exact=True).click()
            page.get_by_label("密码", exact=True).type(email_config['password'], delay=.2)
            page.get_by_role("button", name="登录").click()
            with page.expect_navigation(timeout=90000):
                logger.info('to jump login.')
            page.wait_for_timeout(6000)
            page.close()
            context.close()
            browser.close()
            logger.info(f'end')
    set_timeout(delay=1, cb=action)
    return task


__all__ = ['login_email_and_logout']
