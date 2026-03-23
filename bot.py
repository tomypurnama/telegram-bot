import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import json, datetime, time
from zoneinfo import ZoneInfo

TOKEN = "8538171461:AAGH1HGSMc7BB53MUPw6qGopyKDmZ6zxXdw"

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()
time.sleep(1)

DB_FILE = "database.json"

PASARAN = ["SDY","HKL","TT4","TT5","JWP","JKT"]
REF_LIST = ["TOP","AS7","JT7","BGW","GEM","GSK","HK7","CCL","GAS","KLT","LMB"]

user_mode = {}

# ================= DATABASE =================
def load_db():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

def today():
    return str(datetime.date.today())

def now():
    return datetime.now(ZoneInfo("Asia/Jakarta"))

def rupiah(n):
    return "Rp {:,}".format(n).replace(",", ".")

# ================= INIT USER =================
def init_user(db, chat_id):
    t = today()
    if t not in db:
        db[t] = {"users": {}}
    if str(chat_id) not in db[t]["users"]:
        db[t]["users"][str(chat_id)] = {
            "keluar": {},
            "hasil": 0,
            "ref": {},
            "history": []
        }

# ================= MENU =================
def menu(chat_id):
    m = ReplyKeyboardMarkup(resize_keyboard=True)

    m.row("📊 INVESTASI", "💰 HASIL")
    m.row("📥 REF", "📊 LAPORAN")
    m.row("🗑️ HAPUS")

    bot.send_message(chat_id, "📊 MENU KEUANGAN", reply_markup=m)

# ================= START =================
@bot.message_handler(commands=['start'])
def start(msg):
    menu(msg.chat.id)

# ================= MENU HANDLER =================
@bot.message_handler(func=lambda msg: msg.text in [
    "📊 INVESTASI","💰 HASIL","📥 REF","📊 LAPORAN","🗑️ HAPUS"
])
def menu_handler(msg):
    chat_id = msg.chat.id
    text = msg.text

    if text == "📊 INVESTASI":
        pilih_pasaran(chat_id)

    elif text == "💰 HASIL":
        user_mode[chat_id] = ("HASIL", "HASIL")
        bot.send_message(chat_id, "Input nominal HASIL")

    elif text == "📥 REF":
        pilih_ref(chat_id)

    elif text == "📊 LAPORAN":
        pilih_laporan(chat_id)

    elif text == "🗑️ HAPUS":
        hapus_menu(chat_id)

# ================= PASARAN =================
def pilih_pasaran(chat_id):
    m = ReplyKeyboardMarkup(resize_keyboard=True)

    for i in range(0, len(PASARAN), 2):
        row = []
        row.append(PASARAN[i])
        if i+1 < len(PASARAN):
            row.append(PASARAN[i+1])
        m.row(*row)

    m.row("⬅️ BACK")

    bot.send_message(chat_id, "Pilih Pasaran:", reply_markup=m)

@bot.message_handler(func=lambda msg: msg.text in PASARAN)
def handle_pasaran(msg):
    chat_id = msg.chat.id
    user_mode[chat_id] = ("INVEST", msg.text)
    bot.send_message(chat_id, f"Input nominal {msg.text}")

# ================= REF =================
def pilih_ref(chat_id):
    m = ReplyKeyboardMarkup(resize_keyboard=True)

    for i in range(0, len(REF_LIST), 2):
        row = []
        row.append(REF_LIST[i])
        if i+1 < len(REF_LIST):
            row.append(REF_LIST[i+1])
        m.row(*row)

    m.row("⬅️ BACK")

    bot.send_message(chat_id, "Pilih REF:", reply_markup=m)

@bot.message_handler(func=lambda msg: msg.text in REF_LIST)
def handle_ref(msg):
    chat_id = msg.chat.id
    user_mode[chat_id] = ("REF", msg.text)
    bot.send_message(chat_id, f"Input nominal {msg.text}")

# ================= LAPORAN =================
def pilih_laporan(chat_id):
    m = ReplyKeyboardMarkup(resize_keyboard=True)

    m.row("HARIAN", "MINGGUAN")
    m.row("BULANAN", "⬅️ BACK")

    bot.send_message(chat_id, "📊 PILIH LAPORAN", reply_markup=m)

@bot.message_handler(func=lambda msg: msg.text in ["HARIAN","MINGGUAN","BULANAN"])
def handle_laporan(msg):
    chat_id = msg.chat.id

    if msg.text == "HARIAN":
        laporan(chat_id, 1, "HARIAN")
    elif msg.text == "MINGGUAN":
        laporan(chat_id, 7, "MINGGUAN")
    elif msg.text == "BULANAN":
        laporan(chat_id, 30, "BULANAN")

# ================= BACK =================
@bot.message_handler(func=lambda msg: msg.text == "⬅️ BACK")
def back(msg):
    menu(msg.chat.id)

# ================= INPUT =================
@bot.message_handler(func=lambda msg: msg.text and msg.text.isdigit())
def handle_input(msg):
    chat_id = msg.chat.id

    if chat_id not in user_mode:
        return

    jumlah = int(msg.text)
    dt = now()

    db = load_db()
    init_user(db, chat_id)

    user = db[today()]["users"][str(chat_id)]
    mode, key = user_mode[chat_id]

    if mode == "INVEST":
        user["keluar"][key] = user["keluar"].get(key, 0) + jumlah

    elif mode == "HASIL":
        user["hasil"] += jumlah

    elif mode == "REF":
        user["ref"][key] = user["ref"].get(key, 0) + jumlah

    user["history"].append({
        "type": key,
        "amount": jumlah,
        "time": dt.strftime("%H:%M"),
        "date": dt.strftime("%Y-%m-%d")
    })

    save_db(db)

    bot.send_message(chat_id, f"✅ {key} {rupiah(jumlah)}")
    user_mode.pop(chat_id)
    menu(chat_id)

# ================= LAPORAN =================
def laporan(chat_id, days, label):
    db = load_db()

    keluar, hasil, ref = 0, 0, 0

    for i in range(days):
        d = str(datetime.date.today() - datetime.timedelta(days=i))
        if d not in db:
            continue
        if str(chat_id) not in db[d]["users"]:
            continue

        u = db[d]["users"][str(chat_id)]
        keluar += sum(u["keluar"].values())
        hasil += u["hasil"]
        ref += sum(u["ref"].values())

    profit = hasil + ref - keluar

    bot.send_message(chat_id,
f"""📊 LAPORAN {label}

📅 {today()}

💸 Modal: {rupiah(keluar)}
💰 Hasil: {rupiah(hasil)}
📥 REF: {rupiah(ref)}

📈 Profit: {rupiah(profit)}

🕒 Update: {datetime.datetime.now().strftime("%H:%M")}
""")

# ================= HAPUS =================
def hapus_menu(chat_id):
    db = load_db()
    t = today()

    if t not in db or str(chat_id) not in db[t]["users"]:
        bot.send_message(chat_id, "Tidak ada data")
        return

    history = db[t]["users"][str(chat_id)]["history"]

    if not history:
        bot.send_message(chat_id, "History kosong")
        return

    text = "📋 HISTORY:\n\n"
    for i, h in enumerate(history):
        text += f"{i}. {h['time']} | {h['type']} {rupiah(h['amount'])}\n"

    text += "\nKetik nomor yang ingin dihapus"

    user_mode[chat_id] = ("DELETE", "DEL")

    bot.send_message(chat_id, text)

@bot.message_handler(func=lambda msg: msg.text and msg.text.isdigit())
def handle_delete(msg):
    chat_id = msg.chat.id

    if chat_id not in user_mode:
        return

    mode, _ = user_mode[chat_id]

    if mode != "DELETE":
        return

    idx = int(msg.text)

    db = load_db()
    user = db[today()]["users"][str(chat_id)]

    if idx >= len(user["history"]):
        bot.send_message(chat_id, "Index tidak valid")
        return

    item = user["history"].pop(idx)

    if item["type"] == "HASIL":
        user["hasil"] -= item["amount"]
    elif item["type"] in REF_LIST:
        user["ref"][item["type"]] -= item["amount"]
    else:
        user["keluar"][item["type"]] -= item["amount"]

    save_db(db)

    bot.send_message(chat_id, "🗑️ Data dihapus")
    user_mode.pop(chat_id)
    menu(chat_id)

# ================= RUN =================
bot.infinity_polling()
