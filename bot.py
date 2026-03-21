import telebot
import os

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# ================= DATABASE KALORI ================= #

kalori_db = {
    "nasi": 200,
    "ayam": 250,
    "ayam goreng": 300,
    "mie": 350,
    "telur": 150,
    "roti": 120,
    "kopi": 50,
    "teh": 30,
    "susu": 180,
    "burger": 500,
    "pizza": 600
}

# simpan data user
user_data = {}

# ================= FUNCTION ================= #

def hitung_kalori(text):
    total = 0
    detail = []

    text = text.lower()

    for makanan in kalori_db:
        if makanan in text:
            kal = kalori_db[makanan]
            total += kal
            detail.append(f"{makanan}: {kal} kcal")

    return total, detail

# ================= COMMAND ================= #

@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(msg, "🍽 BOT KALORI AKTIF\n\n/note makanan\n/total\n/reset")

@bot.message_handler(commands=['note'])
def note(msg):
    user_id = msg.chat.id

    try:
        text = msg.text.split(" ", 1)[1]
    except:
        bot.reply_to(msg, "Format: /note nasi ayam goreng")
        return

    total, detail = hitung_kalori(text)

    if user_id not in user_data:
        user_data[user_id] = 0

    user_data[user_id] += total

    hasil = "🍽 Makanan:\n"
    hasil += text + "\n\n"

    hasil += "🔥 Detail:\n"
    hasil += "\n".join(detail) if detail else "Tidak dikenali"

    hasil += f"\n\nTOTAL: {total} kcal"

    bot.reply_to(msg, hasil)

@bot.message_handler(commands=['total'])
def total(msg):
    user_id = msg.chat.id
    total = user_data.get(user_id, 0)

    bot.reply_to(msg, f"📊 Total kalori hari ini:\n🔥 {total} kcal")

@bot.message_handler(commands=['reset'])
def reset(msg):
    user_id = msg.chat.id
    user_data[user_id] = 0

    bot.reply_to(msg, "🔄 Data direset")

print("Bot kalori jalan...")
bot.infinity_polling()
