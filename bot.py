# -*- coding: utf-8 -*-
import telebot
import psycopg2 
import time
import threading 
import os
import requests
import pytz
from flask import Flask 
from telebot import types
from datetime import datetime

# --- WEB SERVER ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000)) # Render အတွက် Port 10000 ပြောင်းထားသည်
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    while True:
        try:
            requests.get("http://0.0.0.0:10000")
        except:
            pass
        time.sleep(300)

# --- CONFIGURATION ---
API_TOKEN = '8132455544:AAGzWeggLonfbu8jZ5wUZfcoRTwv9atAj24'
ADMIN_ID = 8062953746
WITHDRAW_CHANNEL = -1003804050982  

DB_URI = "postgresql://postgres.yoiiszudtnksoeytovrs:UN03LRVCMc1Vx3Uk@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

CHANNELS = [-1003628384777, -1003882533307, -1003804050982]
CHANNEL_LINKS = ["https://t.me/JoKeR_FaN1", "https://t.me/raw_myid_hack_channel", "https://t.me/mini_speed_bot"]
MISSION_CHANNELS = [-1003874895457, -1003821835937, -1003701360564]
MISSION_LINKS = ["https://t.me/outline_vpn_sell", "https://t.me/singal_ch", "https://t.me/lottery_and_slot_channel"]

# --- REWARD SETTINGS ---
NEW_USER_REWARD = 100  
REFER_REWARD = 50      # တစ်ယောက်ခေါ် ၅၀ ကျပ် (ပြင်ဆင်ပြီး)
DAILY_REWARD = 20  
MISSION_REWARD = 50    
MIN_WITHDRAW = 1000    # ၁၀၀၀ ကျပ်မှ စထုတ်ရန် (ပြင်ဆင်ပြီး)

bot = telebot.TeleBot(API_TOKEN, threaded=True, num_threads=50)
mm_tz = pytz.timezone('Asia/Yangon')

# --- DATABASE SETUP ---
def init_db():
    try:
        conn = psycopg2.connect(DB_URI)
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
        markup.add(types.InlineKeyboardButton(f"\U0001F517 Join Channel {i}", url=link))
    return markup

def get_join_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("\u2705 Join ပြီးပါပြီ")
    return markup

def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("\U0001F4B0 လက်ကျန်စစ်ရန်", "\U0001F465 လူခေါ်ငွေရှာ")
    markup.add("\U0001F3E6 ငွေထုတ်ရန်", "\U0001F3AF Missions")
    markup.add("\U0001F381 နေ့စဉ်ဘောနပ်စ်")
    return markup

def get_withdraw_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("\U0001F9E7 KPay", "\U0001F9E7 WavePay")
    markup.add("\U0001F4F2 Phone Bill")
    markup.add("\U0001F519 Back to Menu")
    return markup

# --- USER HANDLERS ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    
    # User အဟောင်းဖြစ်စေ၊ အသစ်ဖြစ်စေ /start နှိပ်ရင် Channel Join ဖို့ အမြဲအရင်ပြမည်
    warning_text = (
        "\u26A0\uFE0F **သတိပေးချက်**\n\n"
        "Bot ကိုအသုံးပြုရန် အောက်ပါ Channel များကို အရင် Join ပေးပါ။\n"
        "**Channel Join မထားပါက ငွေထုတ်ပေးမည်မဟုတ်ပါ။**"
    )
    bot.send_message(user_id, warning_text, reply_markup=get_join_keyboard(), parse_mode="Markdown")
    bot.send_message(user_id, "\U0001F4E2 Channel များ Join ရန်", reply_markup=get_channel_inline_buttons(CHANNEL_LINKS))

    # Referral system (Database ထဲမရှိသေးရင် ထည့်မယ်)
    referrer_id = 0
    if len(message.text.split()) > 1:
        ref_candidate = message.text.split()[1]
        if ref_candidate.isdigit() and int(ref_candidate) != user_id:
            referrer_id = int(ref_candidate)
            
    try:
        conn = psycopg2.connect(DB_URI)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE user_id=%s", (user_id,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (user_id, balance, referred_by, is_rewarded) VALUES (%s, 0, %s, 0)", (user_id, referrer_id))
            conn.commit()
        conn.close()
    except: pass

@bot.message_handler(func=lambda m: m.text == "\u2705 Join ပြီးပါပြီ")
def verify_join(message):
    user_id = message.from_user.id
    # ခလုတ်နှိပ်တဲ့အချိန်မှာ Channel join မ join တကယ်စစ်ဆေးသည်
    if is_joined(user_id, CHANNELS):
        conn = psycopg2.connect(DB_URI)
        cursor = conn.cursor()
        cursor.execute("SELECT referred_by, is_rewarded FROM users WHERE user_id=%s", (user_id,))
        res = cursor.fetchone()
        
        # ပထမဆုံးအကြိမ် verify လုပ်တာဆိုရင် reward ပေးမည်
        if res and res[1] == 0:
            cursor.execute("UPDATE users SET balance = balance + %s, is_rewarded = 1 WHERE user_id = %s", (NEW_USER_REWARD, user_id))
            if res[0] != 0:
                cursor.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (REFER_REWARD, res[0]))
                try: bot.send_message(res[0], f"\u2705 သင်ဖိတ်ခေါ်သူ Join သဖြင့် {REFER_REWARD} Ks ရပါပြီ။")
                except: pass
            conn.commit()
            bot.send_message(user_id, f"\U0001F389 Join မှုအတွက် {NEW_USER_REWARD} Ks လက်ဆောင်ရပါပြီ။")
            
        conn.close()
        bot.send_message(user_id, "\u2705 Join ထားတာ မှန်ကန်ပါတယ်!", reply_markup=get_main_menu())
    else:
        bot.send_message(user_id, "\u26A0\uFE0F မ Join ရသေးပါ။ အကုန် Join ပါ။\n**Channel Join မထားပါက ငွေထုတ်ပေးမည်မဟုတ်ပါ။**", reply_markup=get_channel_inline_buttons(CHANNEL_LINKS))

@bot.message_handler(func=lambda m: m.text == "\U0001F465 လူခေါ်ငွေရှာ")
def invite(message):
    user_id = message.from_user.id
    link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    invite_text = (
        "\U0001F465 **လူခေါ် ငွေရှာ**\n\n"
        f"\U0001F381* သင်ဖိတ်ခေါ်သောသူသည် Channel အားလုံး Join ပြီးပါက {REFER_REWARD} Ks သင့်ထဲသို့ထည့်ပေးမည်။\u2757*\n\n"
        "\U0001F517 **သင့်ဖိတ်ခေါ်လင့် Link**\n"
        f"`{link}`"
    )
    bot.send_message(message.chat.id, invite_text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "\U0001F3E6 ငွေထုတ်ရန်")
def withdraw_start(message):
    user_id = message.from_user.id
    
    # ငွေထုတ်ခါနီး Channel စစ်ဆေးခြင်း
    if not is_joined(user_id, CHANNELS) and user_id != ADMIN_ID:
        text = (
            "\u26A0\uFE0F **သတိပေးချက်**\n\n"
            "**Channel Join မထားပါက ငွေထုတ်ပေးမည်မဟုတ်ပါ။**\n"
            "ကျေးဇူးပြု၍ Channel များသို့ အရင် Join ပါ။"
        )
        bot.send_message(user_id, text, reply_markup=get_channel_inline_buttons(CHANNEL_LINKS), parse_mode="Markdown")
        return

    conn = psycopg2.connect(DB_URI); cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id=%s", (user_id,))
    res = cursor.fetchone(); bal = res[0] if res else 0; conn.close()
    if bal >= MIN_WITHDRAW:
        bot.send_message(user_id, f"\U0001F3E6 လက်ကျန်: {bal} Ks", reply_markup=get_withdraw_menu())
    else: 
        bot.send_message(user_id, f"\u274C အနည်းဆုံး {MIN_WITHDRAW} Ks လိုပါသည်။ လက်ကျန် {bal} Ks သာရှိသည်။")

# --- အခြားအပိုင်းများ (မူလအတိုင်း) ---
@bot.message_handler(func=lambda m: m.text == "\U0001F4B0 လက်ကျန်စစ်ရန်")
def balance(message):
    user_id = message.from_user.id
    conn = psycopg2.connect(DB_URI); cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id=%s", (user_id,))
    res = cursor.fetchone(); bal = res[0] if res else 0
    cursor.execute("SELECT COUNT(*) FROM users WHERE referred_by=%s", (user_id,))
    refer_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users"); total_users = cursor.fetchone()[0]; conn.close()
    bot.send_message(user_id, f"\U0001F4CA **Account Info**\n\n\U0001F4B0 လက်ကျန်: {bal} Ks\n\U0001F465 ဖိတ်ခေါ်သူ: {refer_count} ယောက်\n\U0001F464 စုစုပေါင်းအသုံးပြုသူ: {total_users} ယောက်", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "\U0001F381 နေ့စဉ်ဘောနပ်စ်")
def daily(message):
    user_id = message.from_user.id
    now = int(time.time())
    conn = psycopg2.connect(DB_URI); cursor = conn.cursor()
    cursor.execute("SELECT last_date FROM daily_bonus WHERE user_id=%s", (user_id,))
    data = cursor.fetchone(); cooldown = 86400 
    if data is None or (now - int(data[0])) >= cooldown:
        if data is None: cursor.execute("INSERT INTO daily_bonus (user_id, last_date) VALUES (%s, %s)", (user_id, str(now)))
        else: cursor.execute("UPDATE daily_bonus SET last_date=%s WHERE user_id=%s", (str(now), user_id))
        cursor.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (DAILY_REWARD, user_id))
        conn.commit(); bot.send_message(user_id, f"\U0001F389 Bonus {DAILY_REWARD} Ks ရပါပြီ။")
    else: 
        left = cooldown - (now - int(data[0]))
        bot.send_message(user_id, f"\u231B ၂၄ နာရီ မပြည့်သေးပါ။\n\n\u23F3 ကျန်ရှိချိန် - {left//3600} နာရီ {(left%3600)//60} မိနစ်")
    conn.close()

@bot.message_handler(func=lambda m: m.text == "\U0001F3AF Missions")
def mission_start(message):
    user_id = message.from_user.id
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, link in enumerate(MISSION_LINKS, 1):
        markup.add(types.InlineKeyboardButton(f"\U0001F517 Join Mission {i}", url=link))
    markup.add(types.InlineKeyboardButton("\u2705 စစ်ဆေးမည်", callback_data="verify_mission"))
    bot.send_message(user_id, f"\U0001F3AF **Missions**\nJoin ပါက {MISSION_REWARD} Ks ရမည်။", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "verify_mission")
def verify_mission_callback(call):
    user_id = call.from_user.id
    if is_joined(user_id, MISSION_CHANNELS):
        conn = psycopg2.connect(DB_URI); cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM missions WHERE user_id=%s", (user_id,))
        if cursor.fetchone(): bot.answer_callback_query(call.id, "လုပ်ပြီးပါပြီ။", show_alert=True)
        else:
            cursor.execute("INSERT INTO missions (user_id) VALUES (%s)", (user_id,))
            cursor.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (MISSION_REWARD, user_id))
            conn.commit()
            bot.edit_message_text(f"\u2705 {MISSION_REWARD} Ks ရပါပြီ။", call.message.chat.id, call.message.message_id)
        conn.close()
    else: bot.answer_callback_query(call.id, "\u26A0\uFE0F မ Join ရသေးပါ။", show_alert=True)

@bot.message_handler(func=lambda m: m.text in ["\U0001F9E7 KPay", "\U0001F9E7 WavePay", "\U0001F4F2 Phone Bill"])
def wd_info(message):
    method = message.text
    msg = bot.send_message(message.chat.id, f"[{method}] အတွက် ဖုန်းနံပါတ် ပေးပို့ပါ။", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, wd_amount, method)

def wd_amount(message, method):
    phone_info = message.text
    msg = bot.send_message(message.chat.id, f"ထုတ်မည့်ပမာဏ ရိုက်ပါ။\n(မှတ်ချက် - {method} နံပါတ် {phone_info} သို့ ပို့ပါမည်)")
    bot.register_next_step_handler(msg, wd_final, method, phone_info)

def wd_final(message, method, info):
    if not message.text.isdigit():
        bot.send_message(message.chat.id, "\u274C ဂဏန်းသာ ရိုက်ပါ။", reply_markup=get_main_menu()); return
    amt = int(message.text)
    conn = psycopg2.connect(DB_URI); cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id=%s", (message.from_user.id,))
    res = cursor.fetchone(); current_bal = res[0] if res else 0
    if current_bal >= amt:
        cursor.execute("UPDATE users SET balance = balance - %s WHERE user_id = %s", (amt, message.from_user.id))
        conn.commit()
        username = f"@{message.from_user.username}" if message.from_user.username else "No Username"
        now_mm = datetime.now(mm_tz).strftime('%d/%m/%Y %H:%M')
        withdraw_log = (f"\U0001F514 **ငွေထုတ်တောင်းဆိုမှု**\n\n\U0001F464 Username: {username} (`{message.from_user.id}`)\n\U0001F4B3 Method: {method}\n\U0001F4B5 Amount: {amt} Ks\n\u2139\uFE0F Info: `{info}`\n\n\U0001F4C5 Date: {now_mm} (MM Time)")
        try:
            bot.send_message(WITHDRAW_CHANNEL, withdraw_log, parse_mode="Markdown")
            bot.send_message(message.chat.id, "\u2705 တောင်းဆိုမှု တင်ပြီးပါပြီ။", reply_markup=get_main_menu())
        except: pass
    else: bot.send_message(message.chat.id, f"\u274C လက်ကျန်မလောက်ပါ။ {current_bal} Ks သာရှိသည်။", reply_markup=get_main_menu())
    conn.close()

@bot.message_handler(func=lambda m: m.text == "\U0001F519 Back to Menu")
def back(message): bot.send_message(message.chat.id, "\U0001F3E0 Main Menu", reply_markup=get_main_menu())

# --- ADMIN PANEL ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    text = "\U0001F6E0\uFE0F **Admin Panel**\n\n/broadcast [စာသား]\n/addbalance [id] [amt]\n/stats"
    bot.send_message(ADMIN_ID, text)

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    msg_text = message.text.replace("/broadcast ", "")
    conn = psycopg2.connect(DB_URI); cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users"); users = cursor.fetchall(); conn.close()
    for user in users:
        try: bot.send_message(user[0], msg_text); time.sleep(0.05) 
        except: pass
    bot.send_message(ADMIN_ID, "\u2705 Broadcast ပို့ပြီးပါပြီ။")

@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        args = message.text.split(); target_id, amount = int(args[1]), int(args[2])
        conn = psycopg2.connect(DB_URI); cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (amount, target_id))
        conn.commit(); conn.close()
        bot.send_message(ADMIN_ID, "\u2705 ငွေထည့်သွင်းပြီးပါပြီ။")
    except: bot.send_message(ADMIN_ID, "\u274C Format မှားနေသည်။")

@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id != ADMIN_ID: return
    conn = psycopg2.connect(DB_URI); cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users"); total_users = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(balance) FROM users"); total_bal = cursor.fetchone()[0] or 0
    conn.close()
    bot.send_message(ADMIN_ID, f"\U0001F4CA **Bot Stats**\nUsers: {total_users}\nTotal Balance: {total_bal} Ks")

if __name__ == "__main__":
    init_db()
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()
    print("Bot is starting...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
