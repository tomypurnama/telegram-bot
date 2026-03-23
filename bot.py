import telebot
from telebot.types import ReplyKeyboardMarkup
import sqlite3, datetime
from zoneinfo import ZoneInfo

TOKEN = "8538171461:AAGH1HGSMc7BB53MUPw6qGopyKDmZ6zxXdw"

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

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

user_state = {}

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
    user_state[msg.chat.id] = {"mode": None, "kategori": None}
    menu(msg.chat.id)

# ================= MAIN HANDLER (ANTI BUG) =================
@bot.message_handler(func=lambda msg: True)
def main(msg):
    chat_id = msg.chat.id
    text = msg.text.strip()

    if chat_id not in user_state:
        user_state[chat_id] = {"mode": None, "kategori": None}

    state = user_state[chat_id]

    # ===== MENU =====
    if text == "📊 INVESTASI":
        show_list(chat_id, PASARAN, "INVEST")

    elif text == "💰 HASIL":
        state["mode"] = "HASIL"
        bot.send_message(chat_id, "Input nominal HASIL")

    elif text == "📥 REF":
        show_list(chat_id, REF_LIST, "REF")

    elif text == "📊 LAPORAN":
        show_laporan(chat_id)

    elif text == "📌 RINGKASAN":
        ringkasan(chat_id)

    elif text == "🔄 RESET":
        reset(chat_id)

    elif text == "🗑️ HAPUS":
        hapus_menu(chat_id)

    elif text == "⬅️ BACK":
        menu(chat_id)

    # ===== PILIH INVEST / REF =====
    elif text in PASARAN:
        state["mode"] = "INVEST"
        state["kategori"] = text
        bot.send_message(chat_id, f"Input nominal {text}")

    elif text in REF_LIST:
        state["mode"] = "REF"
        state["kategori"] = text
        bot.send_message(chat_id, f"Input nominal {text}")

    # ===== LAPORAN =====
    elif text in ["HARIAN","MINGGUAN","BULANAN"]:
        days = {"HARIAN":1,"MINGGUAN":7,"BULANAN":30}[text]
        laporan(chat_id, days, text)

    # ===== INPUT ANGKA =====
    elif text.isdigit():
        proses_input(chat_id, int(text))

    else:
        bot.send_message(chat_id, "❗ Pilih menu yang tersedia")

# ================= LIST MENU =================
def show_list(chat_id, data, mode):
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    for i in range(0, len(data), 2):
        m.row(*data[i:i+2])
    m.row("⬅️ BACK")
    bot.send_message(chat_id, "Pilih:", reply_markup=m)

# ================= INPUT =================
def proses_input(chat_id, nominal):
    state = user_state[chat_id]
    mode = state["mode"]
    kategori = state["kategori"]

    if not mode:
        bot.send_message(chat_id, "Pilih menu dulu")
        return

    # DELETE
    if mode == "DELETE":
        delete(chat_id, nominal)
        return

    # INSERT
    cursor.execute("""
    INSERT INTO trx (chat_id,tanggal,tipe,kategori,nominal,waktu)
    VALUES (?,?,?,?,?,?)
    """, (chat_id, today(), mode, kategori, nominal, jam()))

    conn.commit()

    bot.send_message(chat_id, f"✅ {mode} {rupiah(nominal)}")

    user_state[chat_id] = {"mode": None, "kategori": None}
    menu(chat_id)

# ================= GET SUM =================
def get_sum(chat_id, tipe, tanggal):
    cursor.execute("""
    SELECT COALESCE(SUM(nominal),0) FROM trx
    WHERE chat_id=? AND tanggal=? AND tipe=?
    """, (chat_id, tanggal, tipe))
    return cursor.fetchone()[0]

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

# ================= LAPORAN =================
def show_laporan(chat_id):
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.row("HARIAN","MINGGUAN")
    m.row("BULANAN","⬅️ BACK")
    bot.send_message(chat_id, "Pilih laporan:", reply_markup=m)

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

# ================= RESET =================
def reset(chat_id):
    cursor.execute("DELETE FROM trx WHERE chat_id=? AND tanggal=?", (chat_id, today()))
    conn.commit()
    bot.send_message(chat_id, "🔄 Data direset")
    menu(chat_id)

# ================= HAPUS =================
def hapus_menu(chat_id):
    cursor.execute("""
    SELECT id,tipe,kategori,nominal,waktu FROM trx
    WHERE chat_id=? AND tanggal=?
    """, (chat_id, today()))

    rows = cursor.fetchall()

    if not rows:
        bot.send_message(chat_id, "Kosong")
        return

    text = "📋 DATA:\n\n"
    for r in rows:
        text += f"{r[0]}. {r[4]} | {r[1]} {r[2]} {rupiah(r[3])}\n"

    text += "\nKetik ID untuk hapus"

    user_state[chat_id] = {"mode":"DELETE","kategori":None}
    bot.send_message(chat_id, text)

def delete(chat_id, id_data):
    cursor.execute("DELETE FROM trx WHERE id=? AND chat_id=?", (id_data, chat_id))
    conn.commit()
    bot.send_message(chat_id, "🗑️ Dihapus")

    user_state[chat_id] = {"mode": None, "kategori": None}
    menu(chat_id)

# ================= RUN =================
bot.infinity_polling()
