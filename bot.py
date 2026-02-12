# -*- coding: utf-8 -*-
import telebot
import psycopg2 
import time
import threading 
import os
from flask import Flask 
from telebot import types
from datetime import datetime

# --- WEB SERVER FOR RENDER WEB SERVICE ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIGURATION ---
API_TOKEN = '8132455544:AAGzWeggLonfbu8jZ5wUZfcoRTwv9atAj24'
ADMIN_ID = 8062953746
WITHDRAW_CHANNEL = -1003804050982  

# --- DATABASE CONNECTION (Fixed to .com and Port 6543) ---
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

def check_membership(message):
    user_id = message.from_user.id
    if not is_joined(user_id, CHANNELS):
        text = "မင်္ဂလာပါ \U0001F64F\n\nBot ကိုသုံးရန် အောက်ပါ Channel များကို အရင် Join ပေးပါ။\n\nJoin ပြီးလျှင် '\u2705 Join ပြီးပါပြီ' ကို နှိပ်ပါ။"
        bot.send_message(user_id, text, reply_markup=get_join_keyboard())
        bot.send_message(user_id, " \U0001F4E2 Channel များ ", reply_markup=get_channel_inline_buttons(CHANNEL_LINKS))
        return False
    return True

def get_channel_inline_buttons(links):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, link in enumerate(links, 1):
        markup.add(types.InlineKeyboardButton(f" \U0001F517 Join Channel {i}", url=link))
    return markup

def get_join_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("\u2705 Join ပြီးပါပြီ")
    return markup

def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("\U0001F4B0 လက်ကျန်စစ်ရန်", "\U0001F465 လူခေါ်ငွေရှာ")
    markup.add("\U0001F3E6 Ngwe Thout Ran", "\U0001F3AF Missions")
    markup.add("\U0001F381 နေ့စဉ်ဘောနပ်စ်")
    return markup

def get_withdraw_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("\U0001F9E7 KPay", "\U0001F9E7 WavePay")
    markup.add("\U0001F4F2 Phone Bill")
    markup.add("\U0001F519 Back to Menu")
    return markup

# --- ADMIN PANEL ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    text = (
        "\U0001F468\u200D\u2708\ufe0f **Admin Control Panel**\n\n"
        "\U0001F4E2 /broadcast [စာသား] - အားလုံးကို စာပို့ရန်\n"
        "\U0001F4B5 /addbalance [user_id] [ပမာဏ] - ပိုက်ဆံထည့်ရန်\n"
        "\U0001F4CA /stats - စာရင်းကြည့်ရန်"
    )
    bot.send_message(ADMIN_ID, text, parse_mode="Markdown")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    msg_text = message.text.replace("/broadcast ", "")
    if not msg_text or msg_text == "/broadcast": return
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()
    success = 0
    for user in users:
        try:
            bot.send_message(user[0], msg_text)
            success += 1
            time.sleep(0.1)
        except: pass
    bot.send_message(ADMIN_ID, f"\u2705 စုစုပေါင်း {success} ယောက်ကို ပို့ပြီးပါပြီ။")

@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        args = message.text.split()
        target_id, amount = int(args[1]), int(args[2])
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (amount, target_id))
        conn.commit()
        conn.close()
        bot.send_message(ADMIN_ID, f"\u2705 User {target_id} ကို {amount} Ks ထည့်ပြီးပါပြီ။")
    except: bot.send_message(ADMIN_ID, "Error: /addbalance [id] [amount]")

@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id != ADMIN_ID: return
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(balance) FROM users")
    total_balance = cursor.fetchone()[0] or 0
    conn.close()
    bot.send_message(ADMIN_ID, f"\U0001F4CA **Bot Stats**\n\n\U0001F465 အသုံးပြုသူ: {total_users}\n\U0001F4B0 စုစုပေါင်းငွေ: {total_balance} Ks", parse_mode="Markdown")

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

    if is_joined(user_id, CHANNELS):
        bot.send_message(user_id, "\U0001F3E0 Main Menu", reply_markup=get_main_menu())
    else:
        bot.send_message(user_id, "မင်္ဂလာပါ \U0001F64F\nJoin ပေးပါဦး။", reply_markup=get_join_keyboard())
        bot.send_message(user_id, " \U0001F4E2 Channel များ ", reply_markup=get_channel_inline_buttons(CHANNEL_LINKS))

@bot.message_handler(func=lambda m: m.text == "\u2705 Join ပြီးပါပြီ")
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
            try: bot.send_message(res[0], f"\u2705 သင်ဖိတ်ခေါ်သူ Join သဖြင့် {REFER_REWARD} Ks ရပါပြီ။")
            except: pass
        conn.close()
        bot.send_message(user_id, "\u2705 Join ထားတာ မှန်ကန်ပါတယ်!", reply_markup=get_main_menu())
    else:
        bot.send_message(user_id, "\u26A0 မ Join ရသေးပါ။ အကုန် Join ပါ။", reply_markup=get_channel_inline_buttons(CHANNEL_LINKS))

@bot.message_handler(func=lambda m: m.text == "\U0001F4B0 လက်ကျန်စစ်ရန်")
def balance(message):
    if not check_membership(message): return
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id=%s", (message.from_user.id,))
    bal = cursor.fetchone()[0]
    conn.close()
    bot.send_message(message.chat.id, f"\U0001F4B0 **လက်ကျန်: {bal} Ks**", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "\U0001F381 နေ့စဉ်ဘောနပ်စ်")
def daily(message):
    if not check_membership(message): return
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
        bot.send_message(user_id, f"\U0001F389 {DAILY_REWARD} Ks ရရှိပါပြီ။")
    else: bot.send_message(user_id, "\u231B မနက်ဖြန်မှ ပြန်လာယူပါ။")
    conn.close()

@bot.message_handler(func=lambda m: m.text == "\U0001F3AF Missions")
def mission_start(message):
    if not check_membership(message): return
    user_id = message.from_user.id
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM missions WHERE user_id=%s", (user_id,))
    if cursor.fetchone():
        bot.send_message(user_id, "\u274C Mission လုပ်ပြီးပါပြီ။")
        conn.close()
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, link in enumerate(MISSION_LINKS, 1):
        markup.add(types.InlineKeyboardButton(f" \U0001F517 Join Mission Channel {i}", url=link))
    markup.add(types.InlineKeyboardButton("\u2705 စစ်ဆေးမည်", callback_data="verify_mission"))
    bot.send_message(user_id, f"\U0001F3AF **Missions**\nJoin ပါက {MISSION_REWARD} Ks ရမည်။", reply_markup=markup, parse_mode="Markdown")
    conn.close()

@bot.callback_query_handler(func=lambda call: call.data == "verify_mission")
def verify_mission_callback(call):
    user_id = call.from_user.id
    if is_joined(user_id, MISSION_CHANNELS):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO missions (user_id) VALUES (%s) ON CONFLICT DO NOTHING", (user_id,))
        cursor.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (MISSION_REWARD, user_id))
        conn.commit()
        conn.close()
        bot.edit_message_text(f"\u2705 {MISSION_REWARD} Ks ရပါပြီ။", call.message.chat.id, call.message.message_id)
    else: bot.answer_callback_query(call.id, "\u26A0 Join ရန် ကျန်ပါသေးသည်။", show_alert=True)

@bot.message_handler(func=lambda m: m.text == "\U0001F465 လူခေါ်ငွေရှာ")
def invite(message):
    if not check_membership(message): return
    link = f"https://t.me/{bot.get_me().username}?start={message.from_user.id}"
    bot.send_message(message.chat.id, f"\U0001F465 **ဖိတ်ခေါ်လင့်ခ်:**\n`{link}`", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "\U0001F3E6 Ngwe Thout Ran")
def withdraw_start(message):
    if not check_membership(message): return
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id=%s", (message.from_user.id,))
    bal = cursor.fetchone()[0]
    conn.close()
    if bal >= MIN_WITHDRAW:
        bot.send_message(message.chat.id, f"\U0001F3E6 လက်ကျန်: {bal} Ks", reply_markup=get_withdraw_menu())
    else: bot.send_message(message.chat.id, f"\u274C အနည်းဆုံး {MIN_WITHDRAW} Ks လိုပါသည်။")

@bot.message_handler(func=lambda m: m.text in ["\U0001F9E7 KPay", "\U0001F9E7 WavePay", "\U0001F4F2 Phone Bill"])
def wd_info(message):
    msg = bot.send_message(message.chat.id, "ဖုန်းနံပါတ် ပေးပို့ပါ။", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, wd_amount, message.text)

def wd_amount(message, method):
    msg = bot.send_message(message.chat.id, "ထုတ်မည့်ပမာဏ ရိုက်ပါ။")
    bot.register_next_step_handler(msg, wd_final, method, message.text)

def wd_final(message, method, info):
    if not message.text.isdigit():
        bot.send_message(message.chat.id, "ဂဏန်းသာ ရိုက်ပါ။", reply_markup=get_main_menu())
        return
    amt = int(message.text)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id=%s", (message.from_user.id,))
    if cursor.fetchone()[0] >= amt:
        cursor.execute("UPDATE users SET balance = balance - %s WHERE user_id = %s", (amt, message.from_user.id))
        conn.commit()
        bot.send_message(WITHDRAW_CHANNEL, f"\U0001F514 **ငွေထုတ်မှု**\nID: `{message.from_user.id}`\nပမာဏ: {amt}\nနည်းလမ်း: {method}\nနံပါတ်: {info}", parse_mode="Markdown")
        bot.send_message(message.chat.id, "\u2705 တောင်းဆိုမှု တင်ပြီးပါပြီ။", reply_markup=get_main_menu())
    else: bot.send_message(message.chat.id, "\u274C လက်ကျန်မလောက်ပါ။", reply_markup=get_main_menu())
    conn.close()

@bot.message_handler(func=lambda m: m.text == "\U0001F519 Back to Menu")
def back(message): bot.send_message(message.chat.id, "\U0001F3E0 Main Menu", reply_markup=get_main_menu())

# --- BOT STARTING ---
if __name__ == "__main__":
    init_db()
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    print("Bot is starting with Fixed Config on Render...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
