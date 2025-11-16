import telebot
import sqlite3
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = "8575973930:AAHm_dgZ9z1rVMQm_wDnjA9ulXFmeUZHdwg"
bot = telebot.TeleBot(TOKEN)

# Connect to database
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins(
    id INTEGER PRIMARY KEY
    );
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS courses(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT
    );
""")

conn.commit()

# Default admin
def add_default_admin(chat_id):
    cursor.execute("INSERT OR IGNORE INTO admins(id) VALUES(?)", (chat_id,))
    conn.commit()

add_default_admin(123456789)  # Your Telegram ID Here

# Check if admin
def is_admin(uid):
    cursor.execute("SELECT * FROM admins WHERE id=?", (uid,))
    return cursor.fetchone() is not None


@bot.message_handler(commands=['start'])
def start(msg):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    cursor.execute("SELECT name FROM courses")
    data = cursor.fetchall()
    
    for c in data:
        markup.add(KeyboardButton(c[0]))
    
    bot.send_message(msg.chat.id, 
        "👋 خوش آمدی به **Phoenix Assist Bot**\n\n"
        "🎓 برای دریافت اطلاعات دوره‌ها، یک گزینه انتخاب کن:",
        reply_markup=markup,
        parse_mode='Markdown'
    )


@bot.message_handler(commands=['panel'])
def panel(msg):
    if not is_admin(msg.chat.id):
        return bot.send_message(msg.chat.id, "⛔ دسترسی ندارید.")

    bot.send_message(msg.chat.id,
        "🔐 *پنل مدیریت*\n\n"
        "➕ افزودن ادمین: `addadmin ID`\n"
        "➖ حذف ادمین: `removeadmin ID`\n"
        "📚 افزودن دوره: `addcourse نام دوره`",
        parse_mode='Markdown'
    )


@bot.message_handler(func=lambda m: m.text.startswith("addadmin "))
def add_admin(msg):
    if not is_admin(msg.chat.id): return

    try:
        uid = int(msg.text.split()[1])
        cursor.execute("INSERT OR IGNORE INTO admins(id) VALUES(?)", (uid,))
        conn.commit()
        bot.send_message(msg.chat.id, f"✅ ادمین جدید اضافه شد: {uid}")
    except:
        bot.send_message(msg.chat.id, "❌ فرمت نامعتبر")


@bot.message_handler(func=lambda m: m.text.startswith("removeadmin "))
def remove_admin(msg):
    if not is_admin(msg.chat.id): return

    uid = int(msg.text.split()[1])
    cursor.execute("DELETE FROM admins WHERE id=?", (uid,))
    conn.commit()
    bot.send_message(msg.chat.id, f"❌ ادمین حذف شد: {uid}")


@bot.message_handler(func=lambda m: m.text.startswith("addcourse "))
def add_course(msg):
    if not is_admin(msg.chat.id): return

    course_name = msg.text.replace("addcourse ", "")
    cursor.execute("INSERT INTO courses(name) VALUES(?)", (course_name,))
    conn.commit()
    bot.send_message(msg.chat.id, f"📚 دوره اضافه شد:\n➡️ {course_name}")


@bot.message_handler(func=lambda m: True)
def user_message(msg):
    cursor.execute("SELECT name FROM courses")
    courses = [c[0] for c in cursor.fetchall()]

    if msg.text in courses:
        cursor.execute("SELECT id FROM admins")
        admins = cursor.fetchall()

        for a in admins:
            bot.forward_message(a[0], msg.chat.id, msg.message_id)
        bot.send_message(msg.chat.id, "📩 درخواست شما به پشتیبان ارسال شد.")
