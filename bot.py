# -*- coding: utf-8 -*-
import telebot
import sqlite3
import time
import os
from telebot import types
from datetime import datetime
from flask import Flask
from threading import Thread

# --- RENDER PERSISTENT STORAGE SETUP ---
# Render Disk ရဲ့ path ကို /data လို့ ပေးခဲ့ရင် အောက်ကအတိုင်း သုံးရပါမယ်
DB_PATH = "/data/bot_database.db" if os.path.exists("/data") else "bot_database.db"

# --- CONFIGURATION ---
API_TOKEN = '8132455544:AAG5pva1sGNV25FF9LyZRAh-aVXNLbIcHkc'
ADMIN_ID = 8062953746
WITHDRAW_CHANNEL = -1003804050982  

CHANNELS = [-1003628384777, -1003882533307, -1003804050982]
CHANNEL_LINKS = [
    "https://t.me/JoKeR_FaN1",
    "https://t.me/raw_myid_hack_channel",
    "https://t.me/mini_speed_bot"
]

MISSION_CHANNELS = [-1003874895457, -1003821835937, -1003701360564]
MISSION_LINKS = [
    "https://t.me/outline_vpn_sell",
    "https://t.me/singal_ch",
    "https://t.me/lottery_and_slot_channel"
]

REFER_REWARD = 50  
DAILY_REWARD = 20  
MISSION_REWARD = 30 
MIN_WITHDRAW = 500 

bot = telebot.TeleBot(API_TOKEN)

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, referred_by INTEGER, is_rewarded INTEGER DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS daily_bonus 
                      (user_id INTEGER, last_date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS missions 
                      (user_id INTEGER PRIMARY KEY)''')
    conn.commit()
    conn.close()

init_db()

# --- KEEP ALIVE SERVER FOR RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

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
        text = "မင်္ဂလာပါ 🙏\n\nBot ကိုသုံးရန် အောက်ပါ Channel များကို အရင် Join ပေးပါ။\n\nJoin ပြီးလျှင် '\u2705 Join ပြီးပါပြီ' ကို နှိပ်ပါ။"
        bot.send_message(user_id, text, reply_markup=get_join_keyboard())
        bot.send_message(user_id, " Channel များ ", reply_markup=get_channel_inline_buttons(CHANNEL_LINKS))
        return False
    return True

def get_channel_inline_buttons(links):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, link in enumerate(links, 1):
        markup.add(types.InlineKeyboardButton(f" Join Channel {i}", url=link))
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

# --- HANDLERS ---

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    referrer_id = 0
    
    if len(message.text.split()) > 1:
        ref_candidate = message.text.split()[1]
        if ref_candidate.isdigit() and int(ref_candidate) != user_id:
            referrer_id = int(ref_candidate)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, balance, referred_by, is_rewarded) VALUES (?, 0, ?, 0)", (user_id, referrer_id))
        conn.commit()
    conn.close()

    if is_joined(user_id, CHANNELS):
        bot.send_message(user_id, "\U0001F3E0 Main Menu ကိုရောက်ပါပြီ။", reply_markup=get_main_menu())
    else:
        text = "မင်္ဂလာပါ \U0001F64F\n\nBot ကိုသုံးရန် အောက်ပါ Channel များကို အရင် Join ပေးပါ။\n\nJoin ပြီးလျှင် '\u2705 Join ပြီးပါပြီ' ကို နှိပ်ပါ။"
        bot.send_message(user_id, text, reply_markup=get_join_keyboard())
        bot.send_message(user_id, "\U0001F447 Channel များ \U0001F447", reply_markup=get_channel_inline_buttons(CHANNEL_LINKS))

@bot.message_handler(func=lambda m: m.text == "\u2705 Join ပြီးပါပြီ")
def verify_join(message):
    user_id = message.from_user.id
    if is_joined(user_id, CHANNELS):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT referred_by, is_rewarded FROM users WHERE user_id=?", (user_id,))
        res = cursor.fetchone()
        
        if res and res[0] != 0 and res[1] == 0:
            referrer_id = res[0]
            cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (REFER_REWARD, referrer_id))
            cursor.execute("UPDATE users SET is_rewarded = 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            try:
                bot.send_message(referrer_id, f"\u2705 သင်ဖိတ်ခေါ်ထားသူ Join ပြီးပါပြီ။ {REFER_REWARD} Ks လက်ခံရရှိပါသည်။")
            except: pass
        conn.close()
        bot.send_message(message.chat.id, "\u2705 Join ထားတာ မှန်ကန်ပါတယ်။", reply_markup=get_main_menu())
    else:
        bot.send_message(message.chat.id, "\u26A0 Channel အားလုံး မ Join ရသေးပါ။ အကုန် Join ပေးပါ။", reply_markup=get_channel_inline_buttons(CHANNEL_LINKS))

@bot.message_handler(func=lambda m: m.text == "\U0001F3AF Missions")
def mission_start(message):
    if not check_membership(message): return
    user_id = message.from_user.id
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM missions WHERE user_id=?", (user_id,))
    
    if cursor.fetchone():
        bot.send_message(user_id, "\u274C သင်ဤ Mission ကို လုပ်ဆောင်ပြီးပါပြီ။")
        conn.close()
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, link in enumerate(MISSION_LINKS, 1):
        markup.add(types.InlineKeyboardButton(f"\U0001F517 Join Mission Channel {i}", url=link))
    markup.add(types.InlineKeyboardButton("\u2705 စစ်ဆေးမည်", callback_data="verify_mission"))

    text = (
        f"\U0001F3AF **Missions**\n\n"
        f"အောက်ပါ Channel ၃ ခုကို Join ပါက **{MISSION_REWARD} Ks** ရရှိပါမည်။\n"
        f"(တစ်ကြိမ်သာ ရရှိနိုင်ပါသည်)\n\n"
        f"**\u26A0 Channel များအားလုံး Join ပြီးမှ 'စစ်ဆေးမည်' ကိုနှိပ်ပါ။**"
    )
    bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")
    conn.close()

@bot.callback_query_handler(func=lambda call: call.data == "verify_mission")
def verify_mission_callback(call):
    user_id = call.from_user.id
    if is_joined(user_id, MISSION_CHANNELS):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM missions WHERE user_id=?", (user_id,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO missions (user_id) VALUES (?)", (user_id,))
            cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (MISSION_REWARD, user_id))
            conn.commit()
            bot.edit_message_text(f"\u2705 Mission အောင်မြင်ပါသည်။ {MISSION_REWARD} Ks လက်ခံရရှိပါပြီ။", call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "သင်ဤ Mission ကို လုပ်ဆောင်ပြီးသားပါ။", show_alert=True)
        conn.close()
    else:
        bot.answer_callback_query(call.id, "\u26A0 Channel အားလုံး မ Join ရသေးပါ။", show_alert=True)

@bot.message_handler(func=lambda m: m.text == "\U0001F4B0 လက်ကျန်စစ်ရန်")
def balance(message):
    if not check_membership(message): return
    user_id = message.from_user.id
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    data = cursor.fetchone()
    current_balance = data[0] if data else 0
    cursor.execute("SELECT COUNT(*) FROM users WHERE referred_by=?", (user_id,))
    ref_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    conn.close()

    info_text = (
        f"\U0001F4CA **Account Info**\n\n"
        f"\U0001F4B0 **လက်ကျန်: {current_balance} Ks**\n"
        f"\U0001F465 **ဖိတ်ခေါ်ထားသူ: {ref_count} ယောက်**\n"
        f"\U0001F30D **စုစုပေါင်းအသုံးပြုသူ: {total_users} ယောက်**\n\n"
        f"\U0001F381 **လူများများဖိတ်ခေါ်လေ ပိုက်ဆံပိုရလေပါပဲဗျ!**"
    )
    bot.send_message(message.chat.id, info_text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "\U0001F381 နေ့စဉ်ဘောနပ်စ်")
def daily(message):
    if not check_membership(message): return
    user_id = message.from_user.id
    current_time = int(time.time())
    wait_time = 86400 
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT last_date FROM daily_bonus WHERE user_id=?", (user_id,))
    data = cursor.fetchone()
    
    if data is None or (current_time - int(data[0])) >= wait_time:
        if data is None:
            cursor.execute("INSERT INTO daily_bonus (user_id, last_date) VALUES (?, ?)", (user_id, str(current_time)))
        else:
            cursor.execute("UPDATE daily_bonus SET last_date=? WHERE user_id=?", (str(current_time), user_id))
        
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (DAILY_REWARD, user_id))
        conn.commit()
        bot.send_message(message.chat.id, f"\U0001F389 **Bonus {DAILY_REWARD} Ks ရရှိပါပြီ။**", parse_mode="Markdown")
    else:
        remaining_seconds = wait_time - (current_time - int(data[0]))
        hours = remaining_seconds // 3600
        minutes = (remaining_seconds % 3600) // 60
        bot.send_message(message.chat.id, f"\u231B **နေ့စဉ်ဘောနပ်ကို ယူပြီးသားပါ။**\n\n**ပြန်ယူလို့ရမယ့်အချိန်: {hours} နာရီ {minutes} မိနစ်** \u2705", parse_mode="Markdown")
    conn.close()

@bot.message_handler(func=lambda m: m.text == "\U0001F465 လူခေါ်ငွေရှာ")
def invite(message):
    if not check_membership(message): return
    bot_info = bot.get_me()
    link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
    bot.send_message(message.chat.id, f"\U0001F465 **လူခေါ်ငွေရှာ**\n\n\U0001F517 Link: `{link}`", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "\U0001F3E6 ငွေထုတ်ရန်")
def withdraw_start(message):
    if not check_membership(message): return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (message.from_user.id,))
    data = cursor.fetchone()
    current_balance = data[0] if data else 0
    conn.close()
    
    if current_balance >= MIN_WITHDRAW:
        bot.send_message(message.chat.id, f"\U0001F3E6 **ငွေထုတ်ရန်**\n\nလက်ရှိလက်ကျန်: {current_balance} Ks", reply_markup=get_withdraw_menu(), parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, f"\u274C အနည်းဆုံး {MIN_WITHDRAW} Ks လိုအပ်ပါသည်။")

@bot.message_handler(func=lambda m: m.text in ["\U0001F9E7 KPay", "\U0001F9E7 WavePay", "\U0001F4F2 Phone Bill"])
def choose_method(message):
    if not check_membership(message): return
    method = message.text
    msg = bot.send_message(message.chat.id, f"သင်၏ {method} ဖုန်းနံပါတ်ကို ပေးပို့ပါ။", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, process_info, method)

def process_info(message, method):
    if not check_membership(message): return
    info = message.text
    msg = bot.send_message(message.chat.id, "ထုတ်ယူလိုသော 'ငွေပမာဏ' ကို ရိုက်ထည့်ပါ။")
    bot.register_next_step_handler(msg, process_amount, method, info)

def process_amount(message, method, info):
    if not check_membership(message): return
    if not message.text.isdigit():
        bot.send_message(message.chat.id, "\u274C ဂဏန်းသီးသန့်သာ ရိုက်ပါ။", reply_markup=get_main_menu())
        return
    
    amount = int(message.text)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (message.from_user.id,))
    user_balance = cursor.fetchone()[0]
    conn.close()
    
    if user_balance >= amount:
        withdraw_text = (f"\U0001F514 **ငွေထုတ်တောင်းဆိုမှု**\n\n\U0001F464 User: `{message.from_user.id}`\n\U0001F4B0 Amount: {amount} Ks\n\U0001F4B3 Method: {method}\n\U0001F4DD Info: {info}")
        bot.send_message(WITHDRAW_CHANNEL, withdraw_text, parse_mode="Markdown")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, message.from_user.id))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "\u2705 တောင်းဆိုမှုအောင်မြင်ပါသည်။", reply_markup=get_main_menu())
    else:
        bot.send_message(message.chat.id, "\u274C လက်ကျန်ငွေ မလုံလောက်ပါ။", reply_markup=get_main_menu())

@bot.message_handler(func=lambda m: m.text == "\U0001F519 Back to Menu")
def back(message):
    if not check_membership(message): return
    bot.send_message(message.chat.id, "\U0001F3E0 Main Menu", reply_markup=get_main_menu())

if __name__ == "__main__":
    print("Bot is starting on Render...")
    keep_alive() # Flask server ကို background မှာ run ထားခြင်း
    bot.infinity_polling()
