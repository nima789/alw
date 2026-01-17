import os
import requests
from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep

LOGIN_URL = "https://admin.alwaysdata.com/login/?next=/"

# ===== 从环境变量读取 =====
EMAIL = os.getenv("ALWAYS_EMAIL")
PASSWORD = os.getenv("ALWAYS_PASSWORD")
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

if not all([EMAIL, PASSWORD, TG_BOT_TOKEN, TG_CHAT_ID]):
    raise RuntimeError("❌ 缺少环境变量：ALWAYS_EMAIL / ALWAYS_PASSWORD / TG_BOT_TOKEN / TG_CHAT_ID")

def send_telegram(text: str):
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": text
    }
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print("Telegram 发送失败：", e)

# ===== 浏览器配置（老版本 DrissionPage）=====
opts = ChromiumOptions()
opts.headless(True)
opts.set_argument('--disable-gpu')
opts.set_argument('--no-sandbox')
opts.set_argument('--disable-dev-shm-usage')

page = ChromiumPage(opts)

try:
    page.get(LOGIN_URL)

    page.ele('#id_login', timeout=10)
    page.ele('#id_login').input(EMAIL)
    page.ele('#id_password').input(PASSWORD)

    page.run_js("document.getElementById('form-login').submit();")
    sleep(3)

    print("当前 URL:", page.url)

    if '/login' not in page.url:
        msg = "✅ alwaysdata {EMAIL} 登录成功"
        print(msg)
        send_telegram(msg)
    else:
        msg = "❌ alwaysdata {EMAIL} 登录失败（仍在登录页）"
        print(msg)
        send_telegram(msg)

except Exception as e:
    err_msg = f"🔥 alwaysdata {EMAIL} 登录脚本异常：\n{e}"
    print(err_msg)
    send_telegram(err_msg)

finally:
    # page.close()
    pass
