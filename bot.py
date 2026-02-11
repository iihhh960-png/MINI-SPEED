# -*- coding: utf-8 -*-
import telebot
import sqlite3
from telebot import types
from datetime import datetime

# --- CONFIGURATION ---
API_TOKEN = '8132455544:AAGhjdfo3DvXlosgWuBWSJHAh9g1-mY11Fg'
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
MIN_WITHDRAW = 100 

bot = telebot.TeleBot(API_TOKEN)

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, referred_by INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS daily_bonus 
                      (user_id INTEGER, last_date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS missions 
                      (user_id INTEGER PRIMARY KEY)''')
    conn.commit()
    conn.close()

init_db()

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
        #  = \U0001F4E2
        markup.add(types.InlineKeyboardButton(f"\U0001F4E2 Join Channel {i}", url=link))
    return markup

def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    #  = \U0001F4B0,  = \U0001F465,  = \U0001F3E6,  = \U0001F3AF,  = \U0001F381
    markup.add("\U0001F4B0 လက်ကျန်စစ်ရန်", "\U0001F465 လူခေါ်ငွေရှာ")
    markup.add("\U0001F3E6 ငွေထုတ်ရန်", "\U0001F3AF Missions")
    markup.add("\U0001F381 နေ့စဉ်ဘောနပ်စ်")
    return markup

# --- HANDLERS ---

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    referrer_id = None
    
    if len(message.text.split()) > 1:
        ref_candidate = message.text.split()[1]
        if ref_candidate.isdigit() and int(ref_candidate) != user_id:
            referrer_id = int(ref_candidate)

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, referred_by) VALUES (?, ?)", (user_id, referrer_id if referrer_id else 0))
        if referrer_id:
            cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (REFER_REWARD, referrer_id))
            conn.commit()
            try: 
                #  = \U00002705
                bot.send_message(referrer_id, f"\U00002705 လူသစ်ဖိတ်ခေါ်မှုအောင်မြင်၍ {REFER_REWARD} Ks ရရှိပါသည်။")
            except: pass
        conn.commit()
    conn.close()

    if is_joined(user_id, CHANNELS):
        #  = \U0001F3E0
        bot.send_message(user_id, "\U0001F3E0 Main Menu ကိုရောက်ပါပြီ။", reply_markup=get_main_menu())
    else:
        # 🙏 = \U0001F64F
        text = "မင်္ဂလာပါ \U0001F64F\n\nBot ကိုသုံးရန် အောက်ပါ Channel များကို အရင် Join ပေးပါ။"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("\U00002705 Join ပြီးပါပြီ")
        bot.send_message(user_id, text, reply_markup=markup)
        bot.send_message(user_id, "\U0001F447 Channel များ \U0001F447", reply_markup=get_channel_inline_buttons(CHANNEL_LINKS))

@bot.message_handler(func=lambda m: m.text == "\U00002705 Join ပြီးပါပြီ")
def verify_join(message):
    if is_joined(message.from_user.id, CHANNELS):
        bot.send_message(message.chat.id, "\U00002705 Join ထားတာ မှန်ကန်ပါတယ်။", reply_markup=get_main_menu())
    else:
        #  = \U000026A0
        bot.send_message(message.chat.id, "\U000026A0 Channel အားလုံး မ Join ရသေးပါ။", reply_markup=get_channel_inline_buttons(CHANNEL_LINKS))

@bot.message_handler(func=lambda m: m.text == "\U0001F3AF Missions")
def mission_start(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM missions WHERE user_id=?", (user_id,))
    
    if cursor.fetchone():
        bot.send_message(user_id, "\U0000274C သင်ဤ Mission ကို လုပ်ဆောင်ပြီးပါပြီ။")
        conn.close()
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, link in enumerate(MISSION_LINKS, 1):
        #  = \U0001F517
        markup.add(types.InlineKeyboardButton(f"\U0001F517 Join Mission Channel {i}", url=link))
    markup.add(types.InlineKeyboardButton("\U00002705 စစ်ဆေးမည်", callback_data="verify_mission"))

    text = (
        f"\U0001F3AF **Missions**\n\n"
        f"အောက်ပါ Channel ၃ ခုကို Join ပါက **{MISSION_REWARD} Ks** ရရှိပါမည်။\n"
        f"(တစ်ကြိမ်သာ ရရှိနိုင်ပါသည်)"
    )
    bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")
    conn.close()

@bot.callback_query_handler(func=lambda call: call.data == "verify_mission")
def verify_mission_callback(call):
    user_id = call.from_user.id
    if is_joined(user_id, MISSION_CHANNELS):
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM missions WHERE user_id=?", (user_id,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO missions (user_id) VALUES (?)", (user_id,))
            cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (MISSION_REWARD, user_id))
            conn.commit()
            bot.edit_message_text(f"\U00002705 Mission အောင်မြင်ပါသည်။ {MISSION_REWARD} Ks လက်ခံရရှိပါပြီ။", call.message.chat.id, call.message.message_id)
        conn.close()
    else:
        bot.answer_callback_query(call.id, "\U000026A0 Channel အားလုံး မ Join ရသေးပါ။", show_alert=True)

@bot.message_handler(func=lambda m: m.text == "\U0001F4B0 လက်ကျန်စစ်ရန်")
def balance(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    data = cursor.fetchone()
    current_balance = data[0] if data else 0
    cursor.execute("SELECT COUNT(*) FROM users WHERE referred_by=?", (user_id,))
    ref_count = cursor.fetchone()[0]
    conn.close()

    #  = \U0001F4CA
    info_text = (f"\U0001F4CA **Account Info**\n\n\U0001F4B0 **လက်ကျန်: {current_balance} Ks**\n"
                 f"\U0001F465 **ဖိတ်ခေါ်ထားသူ: {ref_count} ယောက်**")
    bot.send_message(message.chat.id, info_text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "\U0001F381 နေ့စဉ်ဘောနပ်စ်")
def daily(message):
    user_id = message.from_user.id
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT last_date FROM daily_bonus WHERE user_id=?", (user_id,))
    data = cursor.fetchone()
    if data is None or data[0] != today:
        if data is None: cursor.execute("INSERT INTO daily_bonus (user_id, last_date) VALUES (?, ?)", (user_id, today))
        else: cursor.execute("UPDATE daily_bonus SET last_date=? WHERE user_id=?", (today, user_id))
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (DAILY_REWARD, user_id))
        conn.commit()
        #  = \U0001F389
        bot.send_message(message.chat.id, f"\U0001F389 Bonus {DAILY_REWARD} Ks ရရှိပါပြီ။")
    else: 
        #  = \U0000231B
        bot.send_message(message.chat.id, "\U0000231B မနက်ဖြန်မှ ပြန်လာခဲ့ပါ။")
    conn.close()

@bot.message_handler(func=lambda m: m.text == "\U0001F465 လူခေါ်ငွေရှာ")
def invite(message):
    bot_info = bot.get_me()
    link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
    bot.send_message(message.chat.id, f"\U0001F465 **လူခေါ်ငွေရှာ**\n\n\U0001F517 Link: `{link}`", parse_mode="Markdown")

print("Bot is running with Unicode Escaped Emojis...")
bot.infinity_polling()

