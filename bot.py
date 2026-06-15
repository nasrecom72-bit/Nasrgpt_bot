import os
import telebot
from openai import OpenAI

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROK_API_KEY = os.environ.get("GROK_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = OpenAI(
    api_key=GROK_API_KEY,
    base_url="https://api.x.ai/v1"
)

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

    user_history[chat_id].append({
        "role": "user",
        "content": user_text
    })

    bot.send_chat_action(chat_id, 'typing')

    try:
        response = client.chat.completions.create(
            model="grok-3",
            messages=[
                {"role": "system", "content": "أنت NasrGPT، مساعد ذكاء اصطناعي ذكي ومفيد يتحدث العربية بطلاقة. أجب بشكل واضح ومختصر وودي."},
                *user_history[chat_id]
            ],
            max_tokens=1000
        )

        reply = response.choices[0].message.content

        user_history[chat_id].append({
            "role": "assistant",
            "content": reply
        })

        bot.reply_to(message, reply)

    except Exception as e:
        bot.reply_to(message, f"⚠️ حدث خطأ: {str(e)}")

bot.infinity_polling()
