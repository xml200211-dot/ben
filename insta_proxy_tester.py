import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import asyncio
import http.server
import socketserver
import threading
import os

# --- الإعدادات ---
# الصق توكن بوت تيليجرام الخاص بك هنا
TELEGRAM_BOT_TOKEN = "1936058114:AAHm19u1R6lv_vShGio-MIo4Z0rjVUoew_U"

# الصق معرف تيليجرام الخاص بك هنا (يجب أن يكون رقماً)
ADMIN_CHAT_ID = 1148797883

# --- إعدادات خادم الويب (للتوافق مع Render) ---
PORT = int(os.environ.get("PORT", 8080))

class KeepAliveHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Beast is alive!")

def run_keep_alive_server():
    with socketserver.TCPServer(("", PORT), KeepAliveHandler) as httpd:
        print(f"✅ خادم الويب يعمل على المنفذ {PORT} لإبقاء البوت حياً.")
        httpd.serve_forever()

# --- تعريف أوامر البوت ---

async def start_command(update, context):
    """
    هذه الدالة يتم استدعاؤها عند إرسال أمر /start
    """
    user_id = update.message.from_user.id
    if user_id == ADMIN_CHAT_ID:
        # الرسالة الترحيبية الجديدة التي طلبتها
        welcome_message = "مرحباً سيدي مهدي، أنا جاهز لتنفيذ أي شيء تريده."
        await update.message.reply_text(welcome_message)
        print("✅ تم إرسال الرسالة الترحيبية إلى المدير.")
    else:
        print(f"⚠️ تم استلام رسالة من مستخدم غير مصرح به: {user_id}")

async def echo_handler(update, context):
    """
    هذه الدالة يتم استدعاؤها عند إرسال أي رسالة نصية
    """
    user_id = update.message.from_user.id
    if user_id == ADMIN_CHAT_ID:
        text = update.message.text
        response = f"صدى: {text}"
        print(f"تم استلام: '{text}' | تم الرد بـ: '{response}'")
        await update.message.reply_text(response)
    else:
        pass

# --- التشغيل الرئيسي ---

def main():
    print("⏳ جاري تشغيل البوت...")

    # تشغيل خادم الويب في خيط منفصل
    keep_alive_thread = threading.Thread(target=run_keep_alive_server)
    keep_alive_thread.daemon = True
    keep_alive_thread.start()

    # إنشاء كائن تطبيق تيليجرام
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # إضافة معالجات الأوامر والرسائل
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_handler))

    print("✅ البوت يعمل الآن. أرسل له رسالة على تيليجرام.")

    # تشغيل البوت
    application.run_polling()

if __name__ == "__main__":
    main()
