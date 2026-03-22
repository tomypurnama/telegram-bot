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

    # 🔥 2 KOLOM
    m.row(
        InlineKeyboardButton("📊 INVESTASI",callback_data="INVEST"),
        InlineKeyboardButton("💰 HASIL",callback_data="HASIL")
    )
    m.row(
        InlineKeyboardButton("📥 REF",callback_data="REF"),
        InlineKeyboardButton("📊 LAPORAN",callback_data="LAPORAN")
    )
    m.row(
        InlineKeyboardButton("🗑️ HAPUS",callback_data="HAPUS")
    )

    bot.send_message(chat_id,"📊 MENU KEUANGAN",reply_markup=m)

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
        for i in range(0,len(PASARAN),2):
            row = []
            row.append(InlineKeyboardButton(PASARAN[i],callback_data=f"INV_{PASARAN[i]}"))
            if i+1 < len(PASARAN):
                row.append(InlineKeyboardButton(PASARAN[i+1],callback_data=f"INV_{PASARAN[i+1]}"))
            m.row(*row)

        bot.send_message(chat_id,"Pilih Pasaran:",reply_markup=m)

    elif data.startswith("INV_"):
        p = data.split("_")[1]
        user_mode[chat_id] = ("INVEST",p)
        bot.send_message(chat_id,f"Input nominal {p}")

    # ===== HASIL =====
    elif data=="HASIL":
        user_mode[chat_id] = ("HASIL","HASIL")
        bot.send_message(chat_id,"Input nominal HASIL")

    # ===== REF =====
    elif data=="REF":
        m = InlineKeyboardMarkup()

        for i in range(0,len(REF_LIST),2):
            row = []
            row.append(InlineKeyboardButton(REF_LIST[i],callback_data=f"REF_{REF_LIST[i]}"))
            if i+1 < len(REF_LIST):
                row.append(InlineKeyboardButton(REF_LIST[i+1],callback_data=f"REF_{REF_LIST[i+1]}"))
            m.row(*row)

        bot.send_message(chat_id,"Pilih REF:",reply_markup=m)

    elif data.startswith("REF_"):
        r = data.split("_")[1]
        user_mode[chat_id] = ("REF",r)
        bot.send_message(chat_id,f"Input nominal {r}")

    # ===== LAPORAN =====
    elif data=="LAPORAN":
        m = InlineKeyboardMarkup()
        m.row(
            InlineKeyboardButton("Harian",callback_data="L1"),
            InlineKeyboardButton("Mingguan",callback_data="L7")
        )
        m.row(
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

# ================= INPUT =================
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
    mode,key = user_mode[chat_id]

    if mode=="INVEST":
        user["keluar"][key] = user["keluar"].get(key,0)+jumlah

    elif mode=="HASIL":
        user["hasil"] += jumlah

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

    keluar,hasil,ref = 0,0,0

    for i in range(days):
        d = str(datetime.date.today()-datetime.timedelta(days=i))
        if d not in db: continue
        if str(chat_id) not in db[d]["users"]: continue

        u = db[d]["users"][str(chat_id)]
        keluar += sum(u["keluar"].values())
        hasil += u["hasil"]
        ref += sum(u["ref"].values())

    profit = hasil + ref - keluar

    bot.send_message(chat_id,
f"""📊 LAPORAN {label}

💸 Modal: {rupiah(keluar)}
💰 Hasil: {rupiah(hasil)}
📥 REF: {rupiah(ref)}

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

    if item["type"]=="HASIL":
        user["hasil"] -= item["amount"]
    elif item["type"] in REF_LIST:
        user["ref"][item["type"]] -= item["amount"]
    else:
        user["keluar"][item["type"]] -= item["amount"]

    save_db(db)

    bot.send_message(chat_id,"🗑️ Dihapus")
    menu(chat_id)

# ================= RUN =================
bot.infinity_polling()
