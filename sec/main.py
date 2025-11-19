# ==============================================================================
#  RUSHER BOT - v1.0 (Optimized for Koyeb)
# ==============================================================================
import os
import requests
import random
import time
import threading
import json
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import re

# --- استيراد مكتبات المتصفح الشبح ---
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller

# --- إعدادات أساسية ---
# هذا هو التوكن الأصلي الذي كنا نستخدمه
RUSHER_TOKEN = "1936058114:AAHm19u1R6lv_vShGio-MIo4Z0rjVUoew_U"
CHAT_ID = "1148797883"

# --- متغيرات الحالة العامة ---
is_running = False
hits = 0
fails = 0
last_event = "Rusher is idle."
start_time = None
current_target = "None"

# --- إعدادات Flask لخادم الويب ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Rusher bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# --- أداة رشق المتابعين (مع السائق التلقائي) ---
def setup_ghost_browser():
    chromedriver_autoinstaller.install()
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver

def rusher_worker(target_username):
    global hits, fails, last_event
    while is_running:
        driver = None
        try:
            last_event = "🚀 Launching Ghost Browser for Wubito..."
            driver = setup_ghost_browser()
            page_url = "https://wubito.com/instagram-takipci-hilesi/"
            driver.get(page_url)
            
            last_event = "Waiting for username field..."
            wait = WebDriverWait(driver, 30)
            username_input = wait.until(EC.presence_of_element_located((By.ID, "username")))
            
            last_event = "Entering username..."
            username_input.send_keys(target_username)
            
            submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Giriş Yap')]")
            submit_button.click()
            
            last_event = "Logging in... Waiting for send button..."
            send_followers_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Takipçi Gönder')]")))
            
            last_event = f"Sending followers to @{target_username}..."
            send_followers_button.click()
            
            time.sleep(10) 
            
            hits += 1
            last_event = f"✅ Success! Followers sent to @{target_username} via Wubito."

            last_event = "Waiting for cooldown period (10 minutes)..."
            time.sleep(600)

        except Exception as e:
            fails += 1
            error_lines = str(e).split('\n')
            last_event = f"❌ Wubito Error: {error_lines[0]}"
            time.sleep(30)
        finally:
            if driver:
                driver.quit()

# --- المدير العام للمهام ودوال البوت ---
def main_task_manager(target):
    global is_running, start_time, current_target, hits, fails
    is_running = True
    start_time = time.time()
    current_target = target
    hits, fails = 0, 0
    worker_thread = threading.Thread(target=rusher_worker, args=(target,))
    worker_thread.start()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['next_action'] = 'rushing_username'
    await update.message.reply_text("🤖 Welcome to Rusher Bot!\nPlease send the Instagram username to start rushing.")

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_running
    if not is_running:
        await update.message.reply_text("Rusher is not running.")
        return
    is_running = False
    await update.message.reply_text("🛑 Stopping rusher... Please wait for the current cycle to finish.")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uptime = "N/A"
    if start_time:
        uptime_seconds = int(time.time() - start_time)
        minutes, seconds = divmod(uptime_seconds, 60)
        uptime = f"{minutes:02}:{seconds:02}"
    speed = 0
    if start_time and (hits + fails) > 0:
        elapsed = time.time() - start_time
        speed = (hits + fails) / elapsed * 60 if elapsed > 0 else 0
    
    status_msg = (f"📊 Rusher Bot Status 📊\n"
                  f"--------------------------------\n"
                  f"🎯 Target: {current_target}\n"
                  f"⏳ Uptime: {uptime}\n"
                  f"--------------------------------\n"
                  f"✅ Hits: {hits}\n"
                  f"❌ Fails: {fails}\n"
                  f"⚡️ Speed: {speed:.1f} attempts/min\n"
                  f"--------------------------------\n"
                  f"💬 Last Event: {last_event}")
    await update.message.reply_text(status_msg)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('next_action') == 'rushing_username':
        if is_running:
            await update.message.reply_text("⚠️ A task is already running. Use /stop to stop it first.")
            return
        username = update.message.text.strip().replace('@', '')
        if not re.match(r'^[a-zA-Z0-9._]{1,30}$', username):
            await update.message.reply_text("Invalid username. Please send a valid Instagram username.")
            return
        context.user_data['next_action'] = None
        await update.message.reply_text(f"🚀 Starting to rush followers for @{username} on Wubito...")
        main_task_manager(username)

def run_bot():
    application = Application.builder().token(RUSHER_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    print("Rusher Bot is up and running...")
    application.run_polling()

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask); flask_thread.daemon = True; flask_thread.start()
    run_bot()
