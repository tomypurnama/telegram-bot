import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import datetime

TOKEN = "8538171461:AAGH1HGSMc7BB53MUPw6qGopyKDmZ6zxXdw"
ADMIN_ID = 1413016663

bot = telebot.TeleBot(TOKEN)

DB_FILE = "database.json"
user_state = {}

PASARAN = ["SDY", "TT4", "TT5", "JWP", "HKL"]

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

# ================= MENU UTAMA =================
def menu(chat_id):
    markup = InlineKeyboardMarkup()

    markup.row(
        InlineKeyboardButton("SDY", callback_data="SDY"),
        InlineKeyboardButton("TT4", callback_data="TT4")
    )
    markup.row(
        InlineKeyboardButton("TT5", callback_data="TT5"),
        InlineKeyboardButton("JWP", callback_data="JWP")
    )
    markup.row(
        InlineKeyboardButton("HKL", callback_data="HKL"),
        InlineKeyboardButton("💰 HASIL", callback_data="HASIL")
    )
    markup.row(
        InlineKeyboardButton("📊 LAPORAN", callback_data="LAPORAN"),
        InlineKeyboardButton("🗑️ HAPUS", callback_data="HAPUS")
    )

    bot.send_message(chat_id, "📊 MENU INVESTASI", reply_markup=markup)

# ================= NOMINAL BUTTON =================
def menu_nominal(chat_id, mode):
    markup = InlineKeyboardMarkup()

    nominal_list = [50000, 100000, 200000, 500000]

    for n in nominal_list:
        markup.add(InlineKeyboardButton(rupiah(n), callback_data=f"NOM_{mode}_{n}"))

    markup.add(InlineKeyboardButton("⬅️ KEMBALI", callback_data="BACK"))

    bot.send_message(chat_id, f"Pilih nominal untuk {mode}", reply_markup=markup)

# ================= START =================
@bot.message_handler(commands=['start'])
def start(msg):
    menu(msg.chat.id)

# ================= CALLBACK =================
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    data = call.data

    # ================= BACK =================
    if data == "BACK":
        menu(chat_id)
        return

    # ================= LAPORAN =================
    if data == "LAPORAN":
        kirim_laporan(chat_id)
        return

    # ================= HAPUS =================
    if data == "HAPUS":
        tampilkan_history(chat_id)
        return

    # ================= PILIH PASARAN =================
    if data in PASARAN or data == "HASIL":
        user_state[chat_id] = data
        menu_nominal(chat_id, data)
        return

    # ================= INPUT NOMINAL =================
    if data.startswith("NOM_"):
        _, mode, jumlah = data.split("_")
        jumlah = int(jumlah)

        db = load_db()
        t = today()

        if t not in db:
            db[t] = {"keluar": {}, "masuk": 0, "history": []}

        if mode == "HASIL":
            db[t]["masuk"] += jumlah
        else:
            if mode not in db[t]["keluar"]:
                db[t]["keluar"][mode] = 0
            db[t]["keluar"][mode] += jumlah

        db[t]["history"].append({
            "type": mode,
            "amount": jumlah
        })

        save_db(db)

        bot.send_message(chat_id, f"✅ {mode} {rupiah(jumlah)} berhasil dicatat")
        menu(chat_id)
        return

    # ================= HAPUS PILIH =================
    if data.startswith("DEL_"):
        index = int(data.split("_")[1])
        hapus_by_index(chat_id, index)
        return

# ================= TAMPILKAN HISTORY =================
def tampilkan_history(chat_id):
    db = load_db()
    t = today()

    if t not in db or not db[t].get("history"):
        bot.send_message(chat_id, "❌ Tidak ada data")
        return

    markup = InlineKeyboardMarkup()

    for i, item in enumerate(db[t]["history"]):
        teks = f"{item['type']} - {rupiah(item['amount'])}"
        markup.add(InlineKeyboardButton(teks, callback_data=f"DEL_{i}"))

    bot.send_message(chat_id, "Pilih yang mau dihapus:", reply_markup=markup)

# ================= HAPUS =================
def hapus_by_index(chat_id, index):
    db = load_db()
    t = today()

    try:
        item = db[t]["history"].pop(index)
    except:
        bot.send_message(chat_id, "❌ Data tidak ditemukan")
        return

    mode = item["type"]
    jumlah = item["amount"]

    if mode == "HASIL":
        db[t]["masuk"] -= jumlah
    else:
        db[t]["keluar"][mode] -= jumlah
        if db[t]["keluar"][mode] <= 0:
            del db[t]["keluar"][mode]

    save_db(db)

    bot.send_message(chat_id, f"🗑️ Dihapus: {mode} {rupiah(jumlah)}")
    menu(chat_id)

# ================= LAPORAN =================
def kirim_laporan(chat_id):
    db = load_db()
    t = today()

    if t not in db:
        bot.send_message(chat_id, "Belum ada data")
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

# ================= RUN =================
bot.infinity_polling()
