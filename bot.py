import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import datetime
import threading
import time

TOKEN = "ISI_TOKEN_KAMU"
ADMIN_ID = 123456789  # ganti chat id kamu

bot = telebot.TeleBot(TOKEN)

DB_FILE = "database.json"
user_state = {}

# ================= DATABASE =================
def load_db():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

def today():
    return str(datetime.date.today())

def rupiah(n):
    return "Rp {:,}".format(n).replace(",", ".")

# ================= MENU =================
def menu(chat_id):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("SDY", callback_data="SDY"),
        InlineKeyboardButton("TTM4", callback_data="TTM4")
    )
    markup.row(
        InlineKeyboardButton("TTM5", callback_data="TTM5"),
        InlineKeyboardButton("HKL", callback_data="HKL")
    )
    markup.row(
        InlineKeyboardButton("HASIL", callback_data="HASIL")
    )
    markup.row(
        InlineKeyboardButton("📊 LAPORAN", callback_data="LAPORAN")
    )

    bot.send_message(chat_id, "📊 MENU INVESTASI", reply_markup=markup)

# ================= START =================
@bot.message_handler(commands=['start'])
def start(msg):
    menu(msg.chat.id)

# ================= BUTTON =================
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    data = call.data

    if data == "LAPORAN":
        kirim_laporan(chat_id)
        return

    user_state[chat_id] = data
    bot.send_message(chat_id, f"Masukkan nominal untuk {data}")

# ================= INPUT =================
@bot.message_handler(func=lambda msg: True)
def handle_input(msg):
    chat_id = msg.chat.id

    if chat_id not in user_state:
        return

    if not msg.text.isdigit():
        return

    jumlah = int(msg.text)
    db = load_db()
    t = today()

    if t not in db:
        db[t] = {"keluar": {}, "masuk": 0}

    mode = user_state[chat_id]

    if mode == "HASIL":
        db[t]["masuk"] += jumlah

        bot.send_message(chat_id,
            f"✅ HASIL MASUK\n+ {rupiah(jumlah)}\n\nTotal: {rupiah(db[t]['masuk'])}"
        )
    else:
        if mode not in db[t]["keluar"]:
            db[t]["keluar"][mode] = 0

        db[t]["keluar"][mode] += jumlah

        bot.send_message(chat_id,
            f"📉 {mode}\n- {rupiah(jumlah)}\n\nTotal: {rupiah(db[t]['keluar'][mode])}"
        )

    save_db(db)
    user_state.pop(chat_id)

    menu(chat_id)

# ================= LAPORAN =================
def kirim_laporan(chat_id):
    db = load_db()
    t = today()

    if t not in db:
        bot.send_message(chat_id, "Belum ada data hari ini")
        return

    keluar_text = ""
    total_keluar = 0

    for k, v in db[t]["keluar"].items():
        keluar_text += f"{k}: {rupiah(v)}\n"
        total_keluar += v

    masuk = db[t]["masuk"]
    saldo = masuk - total_keluar

    bot.send_message(chat_id,
        f"""📊 LAPORAN {t}

📉 Keluar:
{keluar_text}

Total Keluar: {rupiah(total_keluar)}

📈 Masuk: {rupiah(masuk)}

💰 Saldo: {rupiah(saldo)}
"""
    )

# ================= AUTO JAM 00 =================
def auto_report():
    while True:
        now = datetime.datetime.now()
        if now.hour == 0 and now.minute == 0:
            kirim_laporan(ADMIN_ID)
            time.sleep(60)
        time.sleep(10)

threading.Thread(target=auto_report).start()

# ================= RUN =================
bot.infinity_polling()
