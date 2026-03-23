import telebot
from telebot.types import ReplyKeyboardMarkup
import sqlite3, datetime, time
from zoneinfo import ZoneInfo

TOKEN = "8538171461:AAGH1HGSMc7BB53MUPw6qGopyKDmZ6zxXdw"

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()
time.sleep(1)

PASARAN = ["SDY","HKL","TT4","TT5","JWP","JKT"]
REF_LIST = ["TOP","AS7","JT7","BGW","GEM","GSK","HK7","CCL","GAS","KLT","LMB"]

user_mode = {}

# ================= DATABASE =================
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT,
    tanggal TEXT,
    type TEXT,
    kategori TEXT,
    amount INTEGER,
    waktu TEXT
)
""")
conn.commit()

def now():
    return datetime.datetime.now(ZoneInfo("Asia/Jakarta"))

def today():
    return now().strftime("%Y-%m-%d")

def rupiah(n):
    return "Rp {:,}".format(n).replace(",", ".")

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

# ================= MENU =================
@bot.message_handler(func=lambda msg: msg.text in [
    "📊 INVESTASI","💰 HASIL","📥 REF",
    "📊 LAPORAN","📌 RINGKASAN","🔄 RESET","🗑️ HAPUS"
])
def menu_handler(msg):
    chat_id = msg.chat.id

    if msg.text == "📊 INVESTASI":
        pilih_pasaran(chat_id)

    elif msg.text == "💰 HASIL":
        user_mode[chat_id] = ("HASIL", None)
        bot.send_message(chat_id, "Input nominal HASIL")

    elif msg.text == "📥 REF":
        pilih_ref(chat_id)

    elif msg.text == "📊 LAPORAN":
        pilih_laporan(chat_id)

    elif msg.text == "📌 RINGKASAN":
        ringkasan(chat_id)

    elif msg.text == "🔄 RESET":
        reset_data(chat_id)

    elif msg.text == "🗑️ HAPUS":
        hapus_menu(chat_id)

# ================= PASARAN =================
def pilih_pasaran(chat_id):
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    for i in range(0, len(PASARAN), 2):
        m.row(*PASARAN[i:i+2])
    m.row("⬅️ BACK")
    bot.send_message(chat_id, "Pilih Pasaran:", reply_markup=m)

@bot.message_handler(func=lambda msg: msg.text in PASARAN)
def invest(msg):
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
def ref_input(msg):
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
    laporan(msg.chat.id, {"HARIAN":1,"MINGGUAN":7,"BULANAN":30}[msg.text], msg.text)

# ================= INPUT =================
@bot.message_handler(func=lambda msg: msg.text and msg.text.isdigit())
def input_handler(msg):
    chat_id = msg.chat.id

    if chat_id not in user_mode:
        bot.send_message(chat_id, "Pilih menu dulu")
        return

    mode, kategori = user_mode[chat_id]
    jumlah = int(msg.text)

    if mode == "DELETE":
        delete_data(chat_id, jumlah)
        return

    cursor.execute("""
    INSERT INTO data (chat_id,tanggal,type,kategori,amount,waktu)
    VALUES (?,?,?,?,?,?)
    """, (chat_id, today(), mode, kategori, jumlah, now().strftime("%H:%M")))

    conn.commit()

    bot.send_message(chat_id, f"✅ {mode} {rupiah(jumlah)}")
    user_mode.pop(chat_id)
    menu(chat_id)

# ================= RINGKASAN =================
def ringkasan(chat_id):
    cursor.execute("SELECT SUM(amount) FROM data WHERE chat_id=? AND tanggal=? AND type='INVEST'", (chat_id,today()))
    keluar = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(amount) FROM data WHERE chat_id=? AND tanggal=? AND type='HASIL'", (chat_id,today()))
    hasil = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(amount) FROM data WHERE chat_id=? AND tanggal=? AND type='REF'", (chat_id,today()))
    ref = cursor.fetchone()[0] or 0

    profit = hasil + ref - keluar

    bot.send_message(chat_id,
f"""📌 RINGKASAN

💸 Modal: {rupiah(keluar)}
💰 Hasil: {rupiah(hasil)}
📥 REF: {rupiah(ref)}

📈 Profit: {rupiah(profit)}
""")

# ================= RESET =================
def reset_data(chat_id):
    cursor.execute("DELETE FROM data WHERE chat_id=? AND tanggal=?", (chat_id,today()))
    conn.commit()
    bot.send_message(chat_id, "🔄 Data hari ini dihapus")
    menu(chat_id)

# ================= HAPUS =================
def hapus_menu(chat_id):
    cursor.execute("SELECT id,type,kategori,amount,waktu FROM data WHERE chat_id=? AND tanggal=?", (chat_id,today()))
    rows = cursor.fetchall()

    if not rows:
        bot.send_message(chat_id, "Kosong")
        return

    text = "📋 DATA:\n\n"
    for r in rows:
        text += f"{r[0]}. {r[4]} | {r[1]} {r[2]} {rupiah(r[3])}\n"

    text += "\nKetik ID untuk hapus"

    user_mode[chat_id] = ("DELETE", None)
    bot.send_message(chat_id, text)

def delete_data(chat_id, id_data):
    cursor.execute("DELETE FROM data WHERE id=? AND chat_id=?", (id_data,chat_id))
    conn.commit()
    bot.send_message(chat_id, "🗑️ Dihapus")
    user_mode.pop(chat_id)
    menu(chat_id)

# ================= BACK =================
@bot.message_handler(func=lambda msg: msg.text == "⬅️ BACK")
def back(msg):
    menu(msg.chat.id)

# ================= LAPORAN =================
def laporan(chat_id, days, label):
    keluar = hasil = ref = 0

    for i in range(days):
        d = (now() - datetime.timedelta(days=i)).strftime("%Y-%m-%d")

        cursor.execute("SELECT SUM(amount) FROM data WHERE chat_id=? AND tanggal=? AND type='INVEST'", (chat_id,d))
        keluar += cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(amount) FROM data WHERE chat_id=? AND tanggal=? AND type='HASIL'", (chat_id,d))
        hasil += cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(amount) FROM data WHERE chat_id=? AND tanggal=? AND type='REF'", (chat_id,d))
        ref += cursor.fetchone()[0] or 0

    profit = hasil + ref - keluar

    bot.send_message(chat_id,
f"""📊 LAPORAN {label}

💸 Modal: {rupiah(keluar)}
💰 Hasil: {rupiah(hasil)}
📥 REF: {rupiah(ref)}

📈 Profit: {rupiah(profit)}

🕒 {now().strftime("%H:%M")} WIB
""")

# ================= RUN =================
bot.infinity_polling()
