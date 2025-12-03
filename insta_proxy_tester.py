import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import asyncio
import http.server
import socketserver
import threading
import os
import httpx

# ==============================================================================
# --- الإعدادات (املأ هذه الفراغات فقط) ---
# ==============================================================================

# 1. ضع توكن بوت تيليجرام الخاص بك هنا
TELEGRAM_BOT_TOKEN = "1936058114:AAHm19u1R6lv_vShGio-MIo4Z0rjVUoew_U"

# 2. ضع معرف حساب تيليجرام الخاص بك (الأيدي) هنا
ADMIN_CHAT_ID = 1148797883  # استبدل هذا الرقم بالأيدي الخاص بك

# --- إعدادات Replicate (تم تجهيزها بالكامل بالمفتاح الجديد) ---
REPLICATE_API_TOKEN = "r8_dYYdGQiviX6NKpJfmUnKxGHew7OfbaC3De8Jx" 

# --- إعدادات النموذج (لا تغيرها) ---
REPLICATE_MODEL_ID = "nousresearch/nous-hermes-2-mixtral-8x7b-dpo:2752b1b6a468c05c1a82c61393b4c1f42a98453c36a3a9d549989d4193526625"

# ==============================================================================
# --- (لا تقم بتعديل أي شيء تحت هذا الخط) ---
# ==============================================================================

# --- خادم الويب لإبقاء البوت حياً على Render ---
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

async def start_command(update, context):
    user_id = update.message.from_user.id
    if user_id == ADMIN_CHAT_ID:
        welcome_message = "مرحباً سيدي مهدي. لقد ولدت من جديد بمفتاح نظيف. عقلي هو Nous-Hermes-2. أنا جاهز."
        await update.message.reply_text(welcome_message)

async def handle_message(update, context):
    user_id = update.message.from_user.id
    if user_id != ADMIN_CHAT_ID:
        return

    question = update.message.text
    print(f"🧠 (Nous-Hermes/Replicate) تم استلام سؤال: '{question}'")
    thinking_message = await update.message.reply_text("⏳ (Nous-Hermes/Replicate) أفكر في طلبك...")

    try:
        headers = {
            "Authorization": f"Token {REPLICATE_API_TOKEN}",
            "Content-Type": "application/json",
        }
        data = {
            "version": REPLICATE_MODEL_ID.split(":")[1],
            "input": {
                "prompt": f"### Instruction:\n{question}\n\n### Response:",
                "max_new_tokens": 4096,
                "temperature": 0.7,
                "top_p": 0.95,
                "stop_sequences": "### Instruction:",
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.replicate.com/v1/predictions",
                headers=headers,
                json=data,
                timeout=60.0
            )
            response.raise_for_status()
            prediction = response.json()
            
            get_url = prediction["urls"]["get"]
            output = None
            for _ in range(60):
                await asyncio.sleep(3)
                get_response = await client.get(get_url, headers=headers)
                get_response.raise_for_status()
                result = get_response.json()
                
                if result["status"] == "succeeded":
                    output = "".join(result["output"])
                    break
                elif result["status"] in ["failed", "canceled"]:
                    raise Exception(f"فشل التشغيل على Replicate: {result['error']}")
            
            if output is None:
                raise Exception("انتهى وقت الانتظار ولم تكتمل الإجابة من Replicate.")

            await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=thinking_message.message_id, text=output)

    except httpx.HTTPStatusError as e:
        error_message = f"❌ حدث خطأ من Replicate: {e.response.status_code} - {e.response.text}"
        print(error_message)
        await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=thinking_message.message_id, text=error_message)
    except Exception as e:
        error_message = f"❌ حدث خطأ فادح: {e}"
        print(error_message)
        await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=thinking_message.message_id, text=error_message)

def main():
    print("⏳ جاري تشغيل البوت (الإصدار النهائي - مفتاح نظيف)...")
    keep_alive_thread = threading.Thread(target=run_keep_alive_server)
    keep_alive_thread.daemon = True
    keep_alive_thread.start()
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ البوت يعمل الآن وجاهز لاستقبال الأوامر.")
    application.run_polling()

if __name__ == "__main__":
    main()
