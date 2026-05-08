import imaplib
import email
import time
import re
import random
from telebot import TeleBot, types

# আপনার টোকেন দিন
BOT_TOKEN = "8612176083:AAH3zupfuvzYXv3V4oAvEiupOGueCLPiqzc"
bot = TeleBot(BOT_TOKEN)

user_data = {}

def get_otp(text):
    otp = re.findall(r'\b\d{5,6}\b', text)
    return otp[0] if otp else None

def check_gmail_and_send(chat_id):
    data = user_data.get(chat_id)
    if not data:
        bot.send_message(chat_id, "⚠️ আগে জিমেইল সেটআপ করুন! /set কমান্ড দিন।")
        return
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(data['email'], data['pass'])
        mail.select("inbox")
        status, messages = mail.search(None, 'ALL')
        if status == 'OK':
            latest_email_id = messages[0].split()[-1]
            status, data_mail = mail.fetch(latest_email_id, '(RFC822)')
            msg = email.message_from_bytes(data_mail[0][1])
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
            else:
                body = msg.get_payload(decode=True).decode()
            otp_code = get_otp(body)
            if otp_code:
                reply = f"🔐 <b>New Telegram OTP!</b>\n\n📧 <b>Email:</b> {data['email']}\n🔑 <b>Code:</b> <code>{otp_code}</code>\n⏰ {time.strftime('%H:%M:%S')}"
                bot.send_message(chat_id, reply, parse_mode="HTML")
            else:
                bot.send_message(chat_id, "❌ কোনো ওটিপি পাওয়া যায়নি।")
        mail.logout()
    except Exception as e:
        bot.send_message(chat_id, f"❌ লগইন ফেল!\nError: {e}")

@bot.message_handler(commands=['start', 'reset', 'set'])
def start_setup(message):
    msg = bot.send_message(message.chat.id, "📧 আপনার <b>Gmail ID</b> দিন:", parse_mode="HTML")
    bot.register_next_step_handler(msg, process_email)

def process_email(message):
    user_data[message.chat.id] = {'email': message.text}
    msg = bot.send_message(message.chat.id, "🔑 এবার আপনার ১৬ অক্ষরের <b>App Password</b> দিন:", parse_mode="HTML")
    bot.register_next_step_handler(msg, process_password)

def process_password(message):
    user_data[message.chat.id]['pass'] = message.text.replace(" ", "")
    show_main_menu(message.chat.id)

def show_main_menu(chat_id):
    data = user_data.get(chat_id)
    name, domain = data['email'].split('@')
    variation = "".join(random.choice([c.upper(), c.lower()]) for c in name)
    new_mail = f"{variation}@{domain}"
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("📧 Get New Mail", callback_data="check_mail")
    btn2 = types.InlineKeyboardButton("🔄 Create Mail", callback_data="generate_new")
    btn3 = types.InlineKeyboardButton("♻️ Reset Data", callback_data="reset_data")
    markup.add(btn1, btn2)
    markup.add(btn3)
    text = f"🎲 <b>Variation Panel</b>\n\n📧 Original: <code>{data['email']}</code>\n✨ New: <code>{new_mail}</code>\n\n✅ Active on Server!"
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "check_mail":
        check_gmail_and_send(call.message.chat.id)
    elif call.data == "generate_new":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_main_menu(call.message.chat.id)
    elif call.data == "reset_data":
        start_setup(call.message)

bot.infinity_polling()
