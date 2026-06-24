import os
import json
from datetime import datetime
import telebot
from openai import OpenAI

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))  # أضف ADMIN_ID في Railway

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

user_history = {}
USERS_FILE = "users_data.json"

# ─── تتبع المستخدمين ───────────────────────────────────────

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_user(user, is_new=False):
    users = load_users()
    uid = str(user.id)
    if uid not in users:
        users[uid] = {
            "id": user.id,
            "username": user.username or "",
            "first_name": user.first_name or "",
            "joined_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "message_count": 0
        }
    users[uid]["message_count"] += 1
    users[uid]["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)
    return uid not in load_users()  # True إذا كان جديداً

def notify_admin(user, is_new):
    if not ADMIN_ID:
        return
    if is_new:
        msg = (f"🆕 مستخدم جديد انضم!\n"
               f"الاسم: {user.first_name}\n"
               f"يوزر: @{user.username or 'لا يوجد'}\n"
               f"ID: {user.id}\n"
               f"الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        bot.send_message(ADMIN_ID, msg)

# ─── الأوامر ────────────────────────────────────────────────

@bot.message_handler(commands=['start'])
def start(message):
    u = message.from_user
    users = load_users()
    is_new = str(u.id) not in users
    save_user(u)
    if is_new:
        notify_admin(u, is_new=True)

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

@bot.message_handler(commands=['stats'])
def stats(message):
    # if message.from_user.id != ADMIN_ID:
#     return
    users = load_users()
    total = len(users)
    sorted_users = sorted(users.values(),
                          key=lambda x: x.get("last_seen", ""),
                          reverse=True)[:10]
    text = f"📊 إحصائيات NasrGPT\n\n👥 إجمالي المستخدمين: {total}\n\n🕐 آخر 10 نشاطاً:\n"
    for u in sorted_users:
        name = u.get("first_name", "؟")
        uname = f"@{u['username']}" if u.get("username") else "بدون يوزر"
        msgs = u.get("message_count", 0)
        last = u.get("last_seen", "")
        text += f"• {name} ({uname}) | {msgs} رسالة | {last}\n"
    bot.reply_to(message, text)

@bot.message_handler(commands=['users'])
def list_users(message):
    if message.from_user.id != ADMIN_ID:
        return
    users = load_users()
    text = f"👥 قائمة المستخدمين ({len(users)}):\n\n"
    for u in users.values():
        name = u.get("first_name", "؟")
        uname = f"@{u['username']}" if u.get("username") else "بدون يوزر"
        joined = u.get("joined_at", "")
        text += f"• {name} ({uname}) - انضم: {joined}\n"
    bot.reply_to(message, text)

# ─── المحادثة الرئيسية ──────────────────────────────────────

@bot.message_handler(func=lambda m: True)
def handle(message):
    chat_id = message.chat.id
    user_text = message.text
    save_user(message.from_user)

    if chat_id not in user_history:
        user_history[chat_id] = []

    user_history[chat_id].append({"role": "user", "content": user_text})
    bot.send_chat_action(chat_id, 'typing')

    try:
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {"role": "system", "content": "أنت NasrGPT، مساعد ذكاء اصطناعي ذكي ومفيد يتحدث العربية بطلاقة. أجب بشكل واضح ومختصر وودي."},
                *user_history[chat_id]
            ]
        )
        reply = response.choices[0].message.content
        user_history[chat_id].append({"role": "assistant", "content": reply})

        if len(reply) > 4000:
            for i in range(0, len(reply), 4000):
                bot.send_message(chat_id, reply[i:i+4000])
        else:
            bot.reply_to(message, reply)

    except Exception as e:
        bot.reply_to(message, f"⚠️ حدث خطأ: {str(e)}")

bot.infinity_polling()
