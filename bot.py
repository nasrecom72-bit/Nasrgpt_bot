import os
import telebot
import anthropic

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

# تخزين سجل المحادثة لكل مستخدم
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

    # تهيئة السجل إن لم يكن موجوداً
    if chat_id not in user_history:
        user_history[chat_id] = []

    # إضافة رسالة المستخدم للسجل
    user_history[chat_id].append({
        "role": "user",
        "content": user_text
    })

    # إرسال "جاري الكتابة..."
    bot.send_chat_action(chat_id, 'typing')

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system="أنت NasrGPT، مساعد ذكاء اصطناعي ذكي ومفيد يتحدث العربية بطلاقة. أجب بشكل واضح ومختصر وودي.",
            messages=user_history[chat_id]
        )

        reply = response.content[0].text

        # إضافة رد البوت للسجل
        user_history[chat_id].append({
            "role": "assistant",
            "content": reply
        })

        bot.reply_to(message, reply)

    except Exception as e:
        bot.reply_to(message, "⚠️ حدث خطأ، حاول مجدداً لاحقاً.")

bot.infinity_polling()
