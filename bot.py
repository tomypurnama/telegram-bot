import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json, datetime, threading, time

TOKEN = "8538171461:AAGH1HGSMc7BB53MUPw6qGopyKDmZ6zxXdw"

bot = telebot.TeleBot(TOKEN)

DB_FILE = "database.json"

PASARAN = ["SDY", "TM4", "TM5", "JWP", "HKL"]
NOMINAL = [50000, 100000, 200000, 500000]

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

def now():
    return datetime.datetime.now().strftime("%H:%M")

def rupiah(n):
    return "Rp {:,}".format(n).replace(",", ".")

# ================= MENU =================
def menu(chat_id):
    markup = InlineKeyboardMarkup()

    markup.row(
        InlineKeyboardButton("SDY", callback_data="SDY"),
        InlineKeyboardButton("TM4", callback_data="TM4")
    )
    markup.row(
        InlineKeyboardButton("TM5", callback_data="TM5"),
        InlineKeyboardButton("JWP", callback_data="JWP")
    )
    markup.row(
        InlineKeyboardButton("HKL", callback_data="HKL"),
        InlineKeyboardButton("💰 HASIL", callback_data="HASIL")
    )
    markup.row(
        InlineKeyboardButton("📊 LAPORAN", callback_data="LAPORAN"),
        InlineKeyboardButton("📈 GRAFIK", callback_data="GRAFIK")
    )
    markup.row(
        InlineKeyboardButton("🎯 SET TARGET", callback_data="TARGET"),
        InlineKeyboardButton("🗑️ HAPUS", callback_data="HAPUS")
    )

    bot.send_message(chat_id, "📊 MENU INVESTASI", reply_markup=markup)

# ================= NOMINAL =================
def menu_nominal(chat_id, mode):
    markup = InlineKeyboardMarkup()

    for n in NOMINAL:
        markup.add(InlineKeyboardButton(rupiah(n), callback_data=f"NOM_{mode}_{n}"))

    markup.add(InlineKeyboardButton("⬅️ KEMBALI", callback_data="BACK"))

    bot.send_message(chat_id, f"Pilih nominal {mode}", reply_markup=markup)

# ================= START =================
@bot.message_handler(commands=['start'])
def start(msg):
    menu(msg.chat.id)

# ================= CALLBACK =================
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    data = call.data

    if data == "BACK":
        menu(chat_id)
        return

    if data == "LAPORAN":
        kirim_laporan(chat_id)
        return

    if data == "GRAFIK":
        kirim_grafik(chat_id)
        return

    if data == "TARGET":
        set_target(chat_id)
        return

    if data == "HAPUS":
        tampilkan_history(chat_id)
        return

    if data in PASARAN or data == "HASIL":
        menu_nominal(chat_id, data)
        return

    if data.startswith("NOM_"):
        _, mode, jumlah = data.split("_")
        jumlah = int(jumlah)

        db = load_db()
        t = today()

        if t not in db:
            db[t] = {}

        if str(chat_id) not in db[t]:
            db[t][str(chat_id)] = {
                "keluar": {},
                "masuk": 0,
                "history": [],
                "target": 0
            }

        user = db[t][str(chat_id)]

        if mode == "HASIL":
            user["masuk"] += jumlah
        else:
            if mode not in user["keluar"]:
                user["keluar"][mode] = 0
            user["keluar"][mode] += jumlah

        user["history"].append({
            "type": mode,
            "amount": jumlah,
            "time": now()
        })

        save_db(db)

        cek_target(chat_id)

        bot.send_message(chat_id, f"✅ {mode} {rupiah(jumlah)}")
        menu(chat_id)
        return

    if data.startswith("DEL_"):
        index = int(data.split("_")[1])
        hapus(chat_id, index)
        return

# ================= TARGET =================
user_target_input = {}

def set_target(chat_id):
    user_target_input[chat_id] = True
    bot.send_message(chat_id, "Masukkan target profit (angka saja)")

@bot.message_handler(func=lambda msg: True)
def input_target(msg):
    chat_id = msg.chat.id

    if chat_id not in user_target_input:
        return

    if not msg.text.isdigit():
        return

    jumlah = int(msg.text)

    db = load_db()
    t = today()

    if t not in db:
        db[t] = {}

    if str(chat_id) not in db[t]:
        db[t][str(chat_id)] = {"keluar": {}, "masuk": 0, "history": [], "target": 0}

    db[t][str(chat_id)]["target"] = jumlah

    save_db(db)
    user_target_input.pop(chat_id)

    bot.send_message(chat_id, f"🎯 Target diset: {rupiah(jumlah)}")
    menu(chat_id)

def cek_target(chat_id):
    db = load_db()
    t = today()

    user = db[t][str(chat_id)]

    keluar = sum(user["keluar"].values())
    profit = user["masuk"] - keluar

    if user["target"] and profit >= user["target"]:
        bot.send_message(chat_id, f"🎉 TARGET TERCAPAI!\nProfit: {rupiah(profit)}")

# ================= GRAFIK =================
def kirim_grafik(chat_id):
    db = load_db()
    labels = []
    data_profit = []

    for date in sorted(db.keys()):
        if str(chat_id) not in db[date]:
            continue

        user = db[date][str(chat_id)]
        keluar = sum(user["keluar"].values())
        profit = user["masuk"] - keluar

        labels.append(date)
        data_profit.append(profit)

    if not labels:
        bot.send_message(chat_id, "Belum ada data")
        return

    chart_url = f"https://quickchart.io/chart?c={{type:'line',data:{{labels:{labels},datasets:[{{label:'Profit',data:{data_profit}}}]}}}}"

    bot.send_photo(chat_id, chart_url)

# ================= HISTORY =================
def tampilkan_history(chat_id):
    db = load_db()
    t = today()

    if t not in db or str(chat_id) not in db[t]:
        bot.send_message(chat_id, "❌ Tidak ada data")
        return

    history = db[t][str(chat_id)]["history"]

    markup = InlineKeyboardMarkup()

    for i, item in enumerate(history):
        teks = f"{item['time']} | {item['type']} - {rupiah(item['amount'])}"
        markup.add(InlineKeyboardButton(teks, callback_data=f"DEL_{i}"))

    bot.send_message(chat_id, "Pilih yang mau dihapus:", reply_markup=markup)

# ================= HAPUS =================
def hapus(chat_id, index):
    db = load_db()
    t = today()

    user = db[t][str(chat_id)]

    item = user["history"].pop(index)

    if item["type"] == "HASIL":
        user["masuk"] -= item["amount"]
    else:
        user["keluar"][item["type"]] -= item["amount"]

    save_db(db)

    bot.send_message(chat_id, f"🗑️ Dihapus {item['type']} {rupiah(item['amount'])}")
    menu(chat_id)

# ================= RUN =================
bot.infinity_polling()
