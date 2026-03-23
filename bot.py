import telebot
from telebot.types import ReplyKeyboardMarkup
import sqlite3, datetime, time
from zoneinfo import ZoneInfo

TOKEN = "8538171461:AAGH1HGSMc7BB53MUPw6qGopyKDmZ6zxXdw"

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()
time.sleep(1)

# ================= DATABASE =================
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS trx (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT,
    tanggal TEXT,
    tipe TEXT,
    kategori TEXT,
    nominal INTEGER,
    waktu TEXT
)
""")
conn.commit()

# ================= CONFIG =================
PASARAN = ["SDY","HKL","TT4","TT5","JWP","JKT"]
REF_LIST = ["TOP","AS7","JT7","BGW","GEM","GSK","HK7","CCL","GAS","KLT","LMB"]

user_mode = {}

# ================= TIME =================
def now():
    return datetime.datetime.now(ZoneInfo("Asia/Jakarta"))

def today():
    return now().strftime("%Y-%m-%d")

def jam():
    return now().strftime("%H:%M")

def rupiah(n):
    return "Rp {:,}".format(n or 0).replace(",", ".")

# ================= MENU =================
def menu(chat_id):
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.row("📊 INVESTASI", "💰 HASIL")
    m.row("📥 REF", "📊 LAPORAN")
    m.row("📌 RINGKASAN", "🔄 RESET")
    m.row("🗑️ HAPUS")
    bot.send_message(chat_id, "💎 BOT SULTAN", reply_markup=m)

@bot.message_handler(commands=['start'])
def start(msg):
    menu(msg.chat.id)

# ================= MENU HANDLER =================
@bot.message_handler(func=lambda msg: msg.text in [
    "📊 INVESTASI","💰 HASIL","📥 REF",
    "📊 LAPORAN","📌 RINGKASAN","🔄 RESET","🗑️ HAPUS"
])
def menu_handler(msg):
    chat_id = msg.chat.id
    text = msg.text

    if text == "📊 INVESTASI":
        pilih_pasaran(chat_id)

    elif text == "💰 HASIL":
        user_mode[chat_id] = ("HASIL", None)
        bot.send_message(chat_id, "Input nominal HASIL")

    elif text == "📥 REF":
        pilih_ref(chat_id)

    elif text == "📊 LAPORAN":
        pilih_laporan(chat_id)

    elif text == "📌 RINGKASAN":
        ringkasan(chat_id)

    elif text == "🔄 RESET":
        reset(chat_id)

    elif text == "🗑️ HAPUS":
        hapus_menu(chat_id)

# ================= INVEST =================
def pilih_pasaran(chat_id):
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    for i in range(0, len(PASARAN), 2):
        m.row(*PASARAN[i:i+2])
    m.row("⬅️ BACK")
    bot.send_message(chat_id, "Pilih Pasaran:", reply_markup=m)

@bot.message_handler(func=lambda msg: msg.text in PASARAN)
def set_invest(msg):
    user_mode[msg.chat.id] = ("INVEST", msg.text)
    bot.send_message(msg.chat.id, f"Input nominal {msg.text}")

# ================= REF =================
def pilih_ref(chat_id):
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    for i in range(0, len(REF_LIST), 2):
        m.row(*REF_LIST[i:i+2])
    m.row("⬅️ BACK")
    bot.send_message(chat_id, "Pilih REF:", reply_markup=m)

@bot.message_handler(func=lambda msg: msg.text in REF_LIST)
def set_ref(msg):
    user_mode[msg.chat.id] = ("REF", msg.text)
    bot.send_message(msg.chat.id, f"Input nominal {msg.text}")

# ================= LAPORAN =================
def pilih_laporan(chat_id):
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.row("HARIAN", "MINGGUAN")
    m.row("BULANAN", "⬅️ BACK")
    bot.send_message(chat_id, "Pilih laporan:", reply_markup=m)

@bot.message_handler(func=lambda msg: msg.text in ["HARIAN","MINGGUAN","BULANAN"])
def laporan_handler(msg):
    hari = {"HARIAN":1,"MINGGUAN":7,"BULANAN":30}[msg.text]
    laporan(msg.chat.id, hari, msg.text)

# ================= INPUT (FIX UTAMA) =================
@bot.message_handler(func=lambda msg: msg.text and msg.text.isdigit())
def input_data(msg):
    chat_id = msg.chat.id

    if chat_id not in user_mode:
        bot.send_message(chat_id, "Pilih menu dulu")
        return

    tipe, kategori = user_mode[chat_id]
    nominal = int(msg.text)

    if tipe == "DELETE":
        delete(chat_id, nominal)
        return

    cursor.execute("""
    INSERT INTO trx (chat_id,tanggal,tipe,kategori,nominal,waktu)
    VALUES (?,?,?,?,?,?)
    """, (chat_id, today(), tipe, kategori, nominal, jam()))

    conn.commit()

    bot.send_message(chat_id, f"✅ {tipe} {rupiah(nominal)}")
    user_mode.pop(chat_id)
    menu(chat_id)

# ================= RINGKASAN =================
def ringkasan(chat_id):
    keluar = get_sum(chat_id, "INVEST", today())
    hasil = get_sum(chat_id, "HASIL", today())
    ref = get_sum(chat_id, "REF", today())

    profit = hasil + ref - keluar

    bot.send_message(chat_id,
f"""📌 RINGKASAN

💸 Modal: {rupiah(keluar)}
💰 Hasil: {rupiah(hasil)}
📥 REF: {rupiah(ref)}

📈 Profit: {rupiah(profit)}
""")

# ================= GET SUM FIX =================
def get_sum(chat_id, tipe, tanggal):
    cursor.execute("""
    SELECT COALESCE(SUM(nominal),0) FROM trx
    WHERE chat_id=? AND tanggal=? AND tipe=?
    """, (chat_id, tanggal, tipe))
    return cursor.fetchone()[0] or 0

# ================= RESET =================
def reset(chat_id):
    cursor.execute("DELETE FROM trx WHERE chat_id=? AND tanggal=?", (chat_id, today()))
    conn.commit()
    bot.send_message(chat_id, "🔄 Data hari ini dihapus")
    menu(chat_id)

# ================= HAPUS =================
def hapus_menu(chat_id):
    cursor.execute("""
    SELECT id,tipe,kategori,nominal,waktu FROM trx
    WHERE chat_id=? AND tanggal=?
    """, (chat_id, today()))

    data = cursor.fetchall()

    if not data:
        bot.send_message(chat_id, "Kosong")
        return

    text = "📋 DATA:\n\n"
    for d in data:
        text += f"{d[0]}. {d[4]} | {d[1]} {d[2]} {rupiah(d[3])}\n"

    text += "\nKetik ID untuk hapus"

    user_mode[chat_id] = ("DELETE", None)
    bot.send_message(chat_id, text)

def delete(chat_id, id_data):
    cursor.execute("DELETE FROM trx WHERE id=? AND chat_id=?", (id_data, chat_id))
    conn.commit()
    bot.send_message(chat_id, "🗑️ Dihapus")
    user_mode.pop(chat_id)
    menu(chat_id)

# ================= BACK =================
@bot.message_handler(func=lambda msg: msg.text == "⬅️ BACK")
def back(msg):
    menu(msg.chat.id)

# ================= LAPORAN FIX =================
def laporan(chat_id, days, label):
    keluar = hasil = ref = 0

    for i in range(days):
        d = (now() - datetime.timedelta(days=i)).strftime("%Y-%m-%d")

        keluar += get_sum(chat_id, "INVEST", d)
        hasil += get_sum(chat_id, "HASIL", d)
        ref += get_sum(chat_id, "REF", d)

    profit = hasil + ref - keluar

    bot.send_message(chat_id,
f"""📊 LAPORAN {label}

💸 Modal: {rupiah(keluar)}
💰 Hasil: {rupiah(hasil)}
📥 REF: {rupiah(ref)}

📈 Profit: {rupiah(profit)}

🕒 {jam()} WIB
""")

# ================= RUN =================
bot.infinity_polling()
