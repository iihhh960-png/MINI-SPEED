# -*- coding: utf-8 -*-
import telebot
import psycopg2 
import time
import threading 
import os
from flask import Flask 
from telebot import types
from datetime import datetime

# --- WEB SERVER FOR RENDER (CRITICAL FOR LIVE STATUS) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running!"

def run_flask():
    # Render သည် 8080 ကို default ပေးလေ့ရှိသော်လည်း PORT environment ကို သုံးခြင်းက ပိုစိတ်ချရသည်
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIGURATION ---
API_TOKEN = '8132455544:AAGzWeggLonfbu8jZ5wUZfcoRTwv9atAj24'
ADMIN_ID = 8062953746
# ငွေထုတ်တောင်းဆိုမှု ပို့ရမည့် Channel ID
WITHDRAW_CHANNEL = -1003804050982  

# --- DATABASE CONNECTION ---
DB_URI = "postgresql://postgres.yoiiszudtnksoeytovrs:UN03LRVCMc1Vx3Uk@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

CHANNELS = [-1003628384777, -1003882533307, -1003804050982]
CHANNEL_LINKS = ["https://t.me/JoKeR_FaN1", "https://t.me/raw_myid_hack_channel", "https://t.me/mini_speed_bot"]
MISSION_CHANNELS = [-1003874895457, -1003821835937, -1003701360564]
MISSION_LINKS = ["https://t.me/outline_vpn_sell", "https://t.me/singal_ch", "https://t.me/lottery_and_slot_channel"]

REFER_REWARD = 50  
DAILY_REWARD = 20  
MISSION_REWARD = 30 
MIN_WITHDRAW = 500 

bot = telebot.TeleBot(API_TOKEN)

# --- DATABASE SETUP ---
def get_db_connection():
    return psycopg2.connect(DB_URI)

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                          (user_id BIGINT PRIMARY KEY, balance INTEGER DEFAULT 0, referred_by BIGINT, is_rewarded INTEGER DEFAULT 0)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS daily_bonus 
                          (user_id BIGINT PRIMARY KEY, last_date TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS missions 
                          (user_id BIGINT PRIMARY KEY)''')
        conn.commit()
        cursor.close()
        conn.close()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Database error: {e}")

# --- HELPER FUNCTIONS ---
def is_joined(user_id, channel_list):
    for ch_id in channel_list:
        try:
            member = bot.get_chat_member(ch_id, user_id)
            if member.status in ['left', 'kicked']: return False
        except: return False
    return True

def get_channel_inline_buttons(links):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, link in enumerate(links, 1):
        markup.add(types.InlineKeyboardButton(f" Join Channel {i}", url=link))
    return markup

def get_join_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(" Join ပြီးပါပြီ")
    return markup

def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(" လက်ကျန်စစ်ရန်", " လူခေါ်ငွေရှာ")
    markup.add(" Ngwe Thout Ran", " Missions")
    markup.add(" နေ့စဉ်ဘောနပ်စ်")
    return markup

def get_withdraw_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(" KPay", " WavePay")
    markup.add(" Phone Bill")
    markup.add(" Back to Menu")
    return markup

# --- MIDDLEWARE: Channel Join စစ်ဆေးခြင်း ---
@bot.message_handler(func=lambda message: not is_joined(message.from_user.id, CHANNELS))
def force_join(message):
    user_id = message.from_user.id
    text = "မင်္ဂလာပါ 🙏\n\nBot ကိုအသုံးပြုရန် အောက်ပါ Channel များကို အရင် Join ပေးပါ။\nJoin ပြီးမှသာ ငွေရှာလို့ရပါမည်။"
    bot.send_message(user_id, text, reply_markup=get_join_keyboard())
    bot.send_message(user_id, " Channel များ ", reply_markup=get_channel_inline_buttons(CHANNEL_LINKS))

# --- USER HANDLERS ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    referrer_id = 0
    if len(message.text.split()) > 1:
        ref_candidate = message.text.split()[1]
        if ref_candidate.isdigit() and int(ref_candidate) != user_id:
            referrer_id = int(ref_candidate)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE user_id=%s", (user_id,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (user_id, balance, referred_by, is_rewarded) VALUES (%s, 0, %s, 0)", (user_id, referrer_id))
            conn.commit()
        conn.close()
    except: pass

    bot.send_message(user_id, " Main Menu", reply_markup=get_main_menu())

@bot.message_handler(func=lambda m: m.text == " Join ပြီးပါပြီ")
def verify_join(message):
    user_id = message.from_user.id
    if is_joined(user_id, CHANNELS):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT referred_by, is_rewarded FROM users WHERE user_id=%s", (user_id,))
        res = cursor.fetchone()
        if res and res[0] != 0 and res[1] == 0:
            cursor.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (REFER_REWARD, res[0]))
            cursor.execute("UPDATE users SET is_rewarded = 1 WHERE user_id = %s", (user_id,))
            conn.commit()
            try: bot.send_message(res[0], f" သင်ဖိတ်ခေါ်သူ Join သဖြင့် {REFER_REWARD} Ks ရပါပြီ။")
            except: pass
        conn.close()
        bot.send_message(user_id, " Join ထားတာ မှန်ကန်ပါတယ်!", reply_markup=get_main_menu())
    else:
        bot.send_message(user_id, " မ Join ရသေးပါ။ အကုန် Join ပါ။", reply_markup=get_channel_inline_buttons(CHANNEL_LINKS))

@bot.message_handler(func=lambda m: m.text == " လက်ကျန်စစ်ရန်")
def balance(message):
    user_id = message.from_user.id
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id=%s", (user_id,))
    res = cursor.fetchone()
    bal = res[0] if res else 0
    cursor.execute("SELECT COUNT(*) FROM users WHERE referred_by=%s", (user_id,))
    refer_count = cursor.fetchone()[0]
    conn.close()
    bot.send_message(user_id, f" **Account Info**\n\n လက်ကျန်: {bal} Ks\n ဖိတ်ခေါ်သူ: {refer_count} ယောက်", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == " နေ့စဉ်ဘောနပ်စ်")
def daily(message):
    user_id = message.from_user.id
    now = int(time.time())
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT last_date FROM daily_bonus WHERE user_id=%s", (user_id,))
    data = cursor.fetchone()
    if data is None or (now - int(data[0])) >= 86400:
        if data is None: cursor.execute("INSERT INTO daily_bonus (user_id, last_date) VALUES (%s, %s)", (user_id, str(now)))
        else: cursor.execute("UPDATE daily_bonus SET last_date=%s WHERE user_id=%s", (str(now), user_id))
        cursor.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (DAILY_REWARD, user_id))
        conn.commit()
        bot.send_message(user_id, f" Bonus {DAILY_REWARD} Ks ရပါပြီ။")
    else: bot.send_message(user_id, " ၂၄ နာရီ မပြည့်သေးပါ။")
    conn.close()

@bot.message_handler(func=lambda m: m.text == " Missions")
def mission_start(message):
    user_id = message.from_user.id
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, link in enumerate(MISSION_LINKS, 1):
        markup.add(types.InlineKeyboardButton(f" Join Mission {i}", url=link))
    markup.add(types.InlineKeyboardButton(" စစ်ဆေးမည်", callback_data="verify_mission"))
    bot.send_message(user_id, f" **Missions**\nJoin ပါက {MISSION_REWARD} Ks ရမည်။", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "verify_mission")
def verify_mission_callback(call):
    user_id = call.from_user.id
    if is_joined(user_id, MISSION_CHANNELS):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM missions WHERE user_id=%s", (user_id,))
        if cursor.fetchone():
            bot.answer_callback_query(call.id, "လုပ်ပြီးပါပြီ။", show_alert=True)
        else:
            cursor.execute("INSERT INTO missions (user_id) VALUES (%s)", (user_id,))
            cursor.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (MISSION_REWARD, user_id))
            conn.commit()
            bot.edit_message_text(f" {MISSION_REWARD} Ks ရပါပြီ။", call.message.chat.id, call.message.message_id)
        conn.close()
    else: bot.answer_callback_query(call.id, " မ Join ရသေးပါ။", show_alert=True)

@bot.message_handler(func=lambda m: m.text == " လူခေါ်ငွေရှာ")
def invite(message):
    link = f"https://t.me/{bot.get_me().username}?start={message.from_user.id}"
    bot.send_message(message.chat.id, f" **ဖိတ်ခေါ်လင့်ခ်:**\n`{link}`", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == " Ngwe Thout Ran")
def withdraw_start(message):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id=%s", (message.from_user.id,))
    bal = cursor.fetchone()[0]
    conn.close()
    if bal >= MIN_WITHDRAW:
        bot.send_message(message.chat.id, f" လက်ကျန်: {bal} Ks", reply_markup=get_withdraw_menu())
    else: bot.send_message(message.chat.id, f" အနည်းဆုံး {MIN_WITHDRAW} Ks လိုပါသည်။")

@bot.message_handler(func=lambda m: m.text in [" KPay", " WavePay", " Phone Bill"])
def wd_info(message):
    msg = bot.send_message(message.chat.id, "ဖုန်းနံပါတ် ပေးပို့ပါ။", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, wd_amount, message.text)

def wd_amount(message, method):
    msg = bot.send_message(message.chat.id, "ထုတ်မည့်ပမာဏ ရိုက်ပါ။")
    bot.register_next_step_handler(msg, wd_final, method, message.text)

def wd_final(message, method, info):
    if not message.text.isdigit():
        bot.send_message(message.chat.id, " ဂဏန်းသာ ရိုက်ပါ။", reply_markup=get_main_menu())
        return
    amt = int(message.text)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id=%s", (message.from_user.id,))
    current_bal = cursor.fetchone()[0]
    
    if current_bal >= amt:
        cursor.execute("UPDATE users SET balance = balance - %s WHERE user_id = %s", (amt, message.from_user.id))
        conn.commit()
        
        username = f"@{message.from_user.username}" if message.from_user.username else "No Username"
        withdraw_log = (
            f" **ငွေထုတ်ယူမှုအသစ်**\n"
            f" User: {username} (`{message.from_user.id}`)\n"
            f" ပမာဏ: {amt} Ks\n"
            f" နည်းလမ်း: {method}\n"
            f" နံပါတ်: `{info}`\n"
            f" {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )
        
        bot.send_message(WITHDRAW_CHANNEL, withdraw_log, parse_mode="Markdown")
        bot.send_message(message.chat.id, " တောင်းဆိုမှု တင်ပြီးပါပြီ။ Admin မှ မကြာမီ လွှဲပေးပါမည်။", reply_markup=get_main_menu())
    else: 
        bot.send_message(message.chat.id, " လက်ကျန်မလောက်ပါ။", reply_markup=get_main_menu())
    conn.close()

@bot.message_handler(func=lambda m: m.text == " Back to Menu")
def back(message): bot.send_message(message.chat.id, " Main Menu", reply_markup=get_main_menu())

# --- BOT STARTING ---
if __name__ == "__main__":
    init_db()
    
    # 1. Start Flask in background thread
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    print("Bot is starting...")
    
    # 2. Wait a second for network stability
    time.sleep(2)
    
    # 3. စမ်းသပ်စာ ပို့ခြင်း (Channel သို့)
    try:
        test_msg = " **Mini Speed Bot Online!**\n\nBot စနစ် စတင်လည်ပတ်နေပြီဖြစ်သည်။ စာစမ်းသပ်မှု အောင်မြင်ပါသည်။"
        bot.send_message(WITHDRAW_CHANNEL, test_msg, parse_mode="Markdown")
        print("Initial test message sent to channel!")
    except Exception as e:
        print(f"Failed to send test message: {e}")
        
    # 4. Start Polling
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
