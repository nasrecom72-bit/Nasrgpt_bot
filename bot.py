import os
import telebot
import google.generativeai as genai

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
user_history = {}

@bot.message_handler(commands=['start'])
def start(message):
    user_history[message.chat.id] = []
    bot.reply_to(message,
        "👋 مرحباً! أنا NasrGPT\n"
        "🤖 مساعدك الذكي، اسألني أي سؤال!\n\n"
        "📌 الأوامر:\n"
        "/start - بدء محادثة جديدة\n"
        "/clear - مسح سجل المحادثة"
    )

@bot.message_handler(commands=['clear'])
def clear(message):
    user_history[message.chat.id] = []
    bot.reply_to(message, "✅ تم مسح المحادثة، ابدأ من جديد!")

@bot.message_handler(func=lambda m: True)
def handle(message):
    chat_id = message.chat.id
    user_text = message.text

    if chat_id not in user_history:
        user_history[chat_id] = []

    bot.send_chat_action(chat_id, 'typing')

    try:
        chat = model.start_chat(history=user_history[chat_id])
        response = chat.send_message(user_text)
        reply = response.text

        user_history[chat_id] = chat.history

        bot.reply_to(message, reply)

    except Exception as e:
        bot.reply_to(message, f"⚠️ حدث خطأ: {str(e)}")

bot.infinity_polling()
