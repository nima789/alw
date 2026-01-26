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

def verify_login(page, expected_email: str) -> tuple[bool, str]:
    """
    验证登录状态
    返回: (是否成功, 详细信息)
    """
    try:
        current_url = page.url
        print(f"当前 URL: {current_url}")
        
        # 1. 优先检查是否有错误提示
        error_div = page.ele('.errors', timeout=2)
        if error_div:
            error_text = error_div.text.strip().replace('\n', ' ')
            return False, f"登录失败: {error_text}"
        
        # 2. 检查登录成功的关键标志：用户邮箱显示
        user_login_desc = page.ele('.user-login-desc', timeout=3)
        if user_login_desc:
            displayed_email_elem = user_login_desc.ele('tag:span', timeout=1)
            if displayed_email_elem:
                displayed_email = displayed_email_elem.text.strip()
                if displayed_email == expected_email:
                    return True, f"登录成功（用户区域显示: {displayed_email}）"
                else:
                    return True, f"登录成功但邮箱不匹配（显示: {displayed_email}, 预期: {expected_email}）"
            return True, "登录成功（检测到用户区域）"
        
        # 3. 检查是否还在登录页
        if '/login' in current_url:
            if page.ele('#id_login', timeout=1):
                return False, "登录失败（仍在登录页面）"
        
        # 4. 其他成功标志（备用）
        success_indicators = [
            ('a[href*="logout"]', '登出链接'),
            ('nav.nav-menu', '导航栏'),
            ('.dropdown-menu', '账户菜单'),
        ]
        
        for selector, name in success_indicators:
            if page.ele(selector, timeout=2):
                return True, f"登录成功（检测到{name}）"
        
        # 5. 检查会话 Cookie
        cookies = page.cookies()
        if any(c.get('name') == 'sessionid' for c in cookies):
            return True, "登录成功（检测到会话 Cookie）"
        
        # 6. 无法确定状态
        return None, f"登录状态不明（当前 URL: {current_url}）"
        
    except Exception as e:
        return False, f"验证过程异常: {str(e)}"

# ===== 浏览器配置 =====
opts = ChromiumOptions()
opts.headless(True)
opts.set_argument('--disable-gpu')
opts.set_argument('--no-sandbox')
opts.set_argument('--disable-dev-shm-usage')

page = ChromiumPage(opts)

try:
    print(f"开始登录 {EMAIL}...")
    page.get(LOGIN_URL)
    
    # 等待登录表单加载
    login_input = page.ele('#id_login', timeout=10)
    password_input = page.ele('#id_password', timeout=10)
    
    # 填写表单
    login_input.input(EMAIL)
    password_input.input(PASSWORD)
    
    print("提交登录表单...")
    # 提交表单
    page.run_js("document.getElementById('form-login').submit();")
    
    # 等待页面响应
    sleep(5)
    
    # 验证登录结果
    success, detail = verify_login(page, EMAIL)
    
    if success is True:
        msg = f"✅ alwaysdata 登录成功\n账号: {EMAIL}\n{detail}"
        print(msg)
        send_telegram(msg)
    elif success is False:
        msg = f"❌ alwaysdata 登录失败\n账号: {EMAIL}\n{detail}"
        print(msg)
        send_telegram(msg)
    else:  # None
        msg = f"⚠️ alwaysdata 状态不明\n账号: {EMAIL}\n{detail}"
        print(msg)
        send_telegram(msg)
        
except Exception as e:
    err_msg = f"🔥 alwaysdata 登录脚本异常\n账号: {EMAIL}\n错误: {str(e)}"
    print(err_msg)
    send_telegram(err_msg)
    
finally:
    page.quit()
