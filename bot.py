import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json, datetime, threading, time

TOKEN = "8538171461:AAGH1HGSMc7BB53MUPw6qGopyKDmZ6zxXdw"

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()
time.sleep(1)

DB_FILE = "database.json"

PASARAN = ["SDY","TT4","TT5","JWP","HKL","JKT"]
REF_LIST = ["GAS","CCL","KLT","LMB","AS7","JT7","TOP","BGW","GEM","GSK","HK7"]

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

# ================= MENU =================
def menu(chat_id):
    m = InlineKeyboardMarkup()
    m.row(InlineKeyboardButton("📊 LAPORAN",callback_data="LAPORAN"))
    m.row(InlineKeyboardButton("📈 HASIL",callback_data="HASIL_MENU"))
    m.row(InlineKeyboardButton("📥 REF",callback_data="REF_MENU"))
    m.row(InlineKeyboardButton("💳 PAYMENT",callback_data="PAYMENT"))
    m.row(InlineKeyboardButton("🗑️ HAPUS",callback_data="HAPUS"))
    bot.send_message(chat_id,"📊 MENU UTAMA",reply_markup=m)

# ================= START =================
@bot.message_handler(commands=['start'])
def start(msg):
    menu(msg.chat.id)

# ================= INIT USER =================
def init_user(db,chat_id):
    t = today()
    if t not in db: db[t]={"users":{}}
    if str(chat_id) not in db[t]["users"]:
        db[t]["users"][str(chat_id)]={
            "keluar":{},
            "hasil":0,
            "ref":{},
            "history":[],
            "payment":[]
        }

# ================= INPUT PARSE =================
@bot.message_handler(func=lambda m: True)
def handle(msg):
    text = msg.text.upper()
    chat_id = msg.chat.id

    db = load_db()
    init_user(db,chat_id)

    user = db[today()]["users"][str(chat_id)]

    parts = text.split()
    if len(parts)<2: return

    key = parts[0]
    try:
        amount = int(parts[1])
    except:
        return

    # ===== INVESTASI =====
    if key in PASARAN:
        user["keluar"][key]=user["keluar"].get(key,0)+amount
        user["history"].append({"type":key,"amount":amount,"time":now()})

    # ===== HASIL =====
    elif key=="HASIL":
        user["hasil"]+=amount
        user["history"].append({"type":"HASIL","amount":amount,"time":now()})

    # ===== REF =====
    elif key in REF_LIST:
        user["ref"][key]=user["ref"].get(key,0)+amount
        user["history"].append({"type":key,"amount":amount,"time":now()})

    # ===== PAYMENT BAYAR =====
    elif key=="BAYAR":
        nama = parts[1]
        bayar = int(parts[2])
        for p in user["payment"]:
            if p["nama"]==nama:
                p["bayar"]+=bayar

    save_db(db)
    bot.send_message(chat_id,"✅ Tercatat")

# ================= LAPORAN =================
def laporan(chat_id,days=1):
    db = load_db()
    total_keluar,total_hasil,total_ref = 0,0,0

    for i in range(days):
        d = str(datetime.date.today()-datetime.timedelta(days=i))
        if d not in db: continue
        if str(chat_id) not in db[d]["users"]: continue

        u = db[d]["users"][str(chat_id)]

        total_keluar += sum(u["keluar"].values())
        total_hasil += u["hasil"]
        total_ref += sum(u["ref"].values())

    profit = total_hasil+total_ref-total_keluar

    bot.send_message(chat_id,
f"""📊 LAPORAN

Modal: {rupiah(total_keluar)}
Hasil: {rupiah(total_hasil)}
REF: {rupiah(total_ref)}

💰 Profit: {rupiah(profit)}"""
)

# ================= CALLBACK =================
@bot.callback_query_handler(func=lambda c:True)
def cb(call):
    chat_id = call.message.chat.id
    data = call.data

    if data=="LAPORAN": laporan(chat_id,1)

    elif data=="HASIL_MENU":
        m=InlineKeyboardMarkup()
        m.row(
            InlineKeyboardButton("Harian",callback_data="H1"),
            InlineKeyboardButton("Mingguan",callback_data="H7"),
            InlineKeyboardButton("Bulanan",callback_data="H30")
        )
        bot.send_message(chat_id,"📈 PILIH PERIODE",reply_markup=m)

    elif data=="H1": laporan(chat_id,1)
    elif data=="H7": laporan(chat_id,7)
    elif data=="H30": laporan(chat_id,30)

    elif data=="REF_MENU":
        bot.send_message(chat_id,"Gunakan format: GAS 50000 dll")

    elif data=="PAYMENT":
        bot.send_message(chat_id,"Format:\nTAMBAH Nama Nominal Tanggal\nBAYAR Nama Nominal")

    elif data=="HAPUS":
        hapus_menu(chat_id)

# ================= HAPUS =================
def hapus_menu(chat_id):
    db=load_db()
    t=today()

    if t not in db: return
    if str(chat_id) not in db[t]["users"]: return

    history=db[t]["users"][str(chat_id)]["history"]

    m=InlineKeyboardMarkup()
    for i,h in enumerate(history):
        txt=f"{h['time']} {h['type']} {rupiah(h['amount'])}"
        m.add(InlineKeyboardButton(txt,callback_data=f"DEL_{i}"))

    bot.send_message(chat_id,"Pilih hapus:",reply_markup=m)

@bot.callback_query_handler(func=lambda c:c.data.startswith("DEL_"))
def del_data(call):
    chat_id=call.message.chat.id
    idx=int(call.data.split("_")[1])

    db=load_db()
    user=db[today()]["users"][str(chat_id)]

    item=user["history"].pop(idx)

    if item["type"]=="HASIL":
        user["hasil"]-=item["amount"]
    elif item["type"] in REF_LIST:
        user["ref"][item["type"]]-=item["amount"]
    else:
        user["keluar"][item["type"]]-=item["amount"]

    save_db(db)
    bot.send_message(chat_id,"🗑️ Dihapus")
    menu(chat_id)

# ================= AUTO RESET =================
def auto():
    while True:
        now=datetime.datetime.now()
        if now.hour==0 and now.minute==0:
            print("RESET")
            time.sleep(60)
        time.sleep(10)

threading.Thread(target=auto).start()

# ================= RUN =================
bot.infinity_polling()
