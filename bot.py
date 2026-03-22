import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json, datetime, time

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
        return json.load(open(DB_FILE))
    except:
        return {}

def save_db(db):
    json.dump(db, open(DB_FILE,"w"), indent=2)

def today():
    return str(datetime.date.today())

def now():
    return datetime.datetime.now().strftime("%H:%M")

def rupiah(n):
    return "Rp {:,}".format(n).replace(",", ".")

# ================= INIT =================
def init_user(db,chat_id):
    t = today()
    if t not in db: db[t]={"users":{}}
    if str(chat_id) not in db[t]["users"]:
        db[t]["users"][str(chat_id)]={
            "keluar":{},
            "hasil":0,
            "ref":{},
            "history":[]
        }

# ================= MENU =================
def menu(chat_id):
    m = InlineKeyboardMarkup()
    m.row(InlineKeyboardButton("📊 INVESTASI",callback_data="INVEST"))
    m.row(InlineKeyboardButton("📥 REF",callback_data="REF"))
    m.row(InlineKeyboardButton("📊 LAPORAN",callback_data="LAPORAN"))
    m.row(InlineKeyboardButton("🗑️ HAPUS",callback_data="HAPUS"))
    bot.send_message(chat_id,"📊 MENU UTAMA",reply_markup=m)

# ================= START =================
@bot.message_handler(commands=['start'])
def start(msg):
    menu(msg.chat.id)

# ================= CALLBACK =================
@bot.callback_query_handler(func=lambda c:True)
def cb(call):
    chat_id = call.message.chat.id
    data = call.data

    # ===== INVESTASI =====
    if data=="INVEST":
        m = InlineKeyboardMarkup()
        for p in PASARAN:
            m.add(InlineKeyboardButton(p,callback_data=f"INV_{p}"))
        bot.send_message(chat_id,"Pilih Pasaran:",reply_markup=m)

    elif data.startswith("INV_"):
        pasaran = data.split("_")[1]
        user_mode[chat_id] = ("INVEST",pasaran)
        bot.send_message(chat_id,f"Input nominal {pasaran}")

    # ===== REF =====
    elif data=="REF":
        m = InlineKeyboardMarkup()
        for r in REF_LIST:
            m.add(InlineKeyboardButton(r,callback_data=f"REF_{r}"))
        bot.send_message(chat_id,"Pilih REF:",reply_markup=m)

    elif data.startswith("REF_"):
        ref = data.split("_")[1]
        user_mode[chat_id] = ("REF",ref)
        bot.send_message(chat_id,f"Input nominal {ref}")

    # ===== LAPORAN =====
    elif data=="LAPORAN":
        m = InlineKeyboardMarkup()
        m.row(
            InlineKeyboardButton("Harian",callback_data="L1"),
            InlineKeyboardButton("Mingguan",callback_data="L7"),
            InlineKeyboardButton("Bulanan",callback_data="L30")
        )
        bot.send_message(chat_id,"📊 PILIH LAPORAN",reply_markup=m)

    elif data=="L1": laporan(chat_id,1,"HARIAN")
    elif data=="L7": laporan(chat_id,7,"MINGGUAN")
    elif data=="L30": laporan(chat_id,30,"BULANAN")

    # ===== HAPUS =====
    elif data=="HAPUS":
        hapus_menu(chat_id)

    elif data.startswith("DEL_"):
        idx=int(data.split("_")[1])
        hapus(chat_id,idx)

# ================= INPUT MANUAL =================
@bot.message_handler(func=lambda m:True)
def input_nominal(msg):
    chat_id = msg.chat.id

    if chat_id not in user_mode:
        return

    if not msg.text.isdigit():
        bot.send_message(chat_id,"Masukkan angka saja")
        return

    jumlah = int(msg.text)

    db = load_db()
    init_user(db,chat_id)

    user = db[today()]["users"][str(chat_id)]
    mode, key = user_mode[chat_id]

    if mode=="INVEST":
        user["keluar"][key] = user["keluar"].get(key,0)+jumlah

    elif mode=="REF":
        user["ref"][key] = user["ref"].get(key,0)+jumlah

    user["history"].append({
        "type": key,
        "amount": jumlah,
        "time": now()
    })

    save_db(db)

    bot.send_message(chat_id,f"✅ {key} {rupiah(jumlah)}")
    user_mode.pop(chat_id)
    menu(chat_id)

# ================= LAPORAN =================
def laporan(chat_id,days,label):
    db = load_db()

    total_keluar,total_ref = 0,0

    for i in range(days):
        d = str(datetime.date.today()-datetime.timedelta(days=i))
        if d not in db: continue
        if str(chat_id) not in db[d]["users"]: continue

        u = db[d]["users"][str(chat_id)]
        total_keluar += sum(u["keluar"].values())
        total_ref += sum(u["ref"].values())

    profit = total_ref - total_keluar

    bot.send_message(chat_id,
f"""📊 LAPORAN {label}

💸 Modal: {rupiah(total_keluar)}
💰 Pemasukan (REF): {rupiah(total_ref)}

📈 Profit: {rupiah(profit)}
"""
)

# ================= HAPUS =================
def hapus_menu(chat_id):
    db = load_db()
    t = today()

    if t not in db or str(chat_id) not in db[t]["users"]:
        bot.send_message(chat_id,"Tidak ada data")
        return

    history = db[t]["users"][str(chat_id)]["history"]

    m = InlineKeyboardMarkup()

    for i,h in enumerate(history):
        txt = f"{h['time']} {h['type']} {rupiah(h['amount'])}"
        m.add(InlineKeyboardButton(txt,callback_data=f"DEL_{i}"))

    bot.send_message(chat_id,"Pilih data:",reply_markup=m)

def hapus(chat_id,idx):
    db = load_db()
    user = db[today()]["users"][str(chat_id)]

    item = user["history"].pop(idx)

    if item["type"] in REF_LIST:
        user["ref"][item["type"]] -= item["amount"]
    else:
        user["keluar"][item["type"]] -= item["amount"]

    save_db(db)

    bot.send_message(chat_id,"🗑️ Dihapus")
    menu(chat_id)

# ================= RUN =================
bot.infinity_polling()
