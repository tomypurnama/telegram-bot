import telebot
import os
import dns.resolver
from datetime import datetime
import threading
import time

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

domains = []
last_status = {}
chat_id_global = None

INTERVAL = 300  # 5 menit

def cek_nawala(domain):
    resolver = dns.resolver.Resolver()

    # coba DNS Nawala
    resolver.nameservers = ["180.131.144.144"]

    try:
        resolver.resolve(domain, "A")
        return "safe"
    except:
        pass

    # fallback DNS global
    resolver.nameservers = ["8.8.8.8"]

    try:
        resolver.resolve(domain, "A")
        return "safe"
    except dns.resolver.NXDOMAIN:
        return "blocked"
    except:
        return "error"

# ================= AUTO CHECK ================= #

def auto_check():
    global last_status

    while True:
        if not domains or not chat_id_global:
            time.sleep(10)
            continue

        for d in domains:
            status = cek_nawala(d)
            old = last_status.get(d)

            if old and old != status:
                msg = f"🚨 STATUS CHANGE\n\n{d}\n{old.upper()} → {status.upper()}\n⏱ {(datetime.utcnow().replace(hour=(datetime.utcnow().hour+7)%24)).strftime('%H:%M:%S')}"
                bot.send_message(chat_id_global, msg)

            last_status[d] = status

        time.sleep(INTERVAL)

threading.Thread(target=auto_check, daemon=True).start()

# ================= COMMAND ================= #

@bot.message_handler(commands=['start'])
def start(msg):
    global chat_id_global
    chat_id_global = msg.chat.id
    bot.reply_to(msg, "🤖 BOT NAWALA MONITOR READY\n\n/add domain.com\n/check")

@bot.message_handler(commands=['add'])
def add_domain(msg):
    global chat_id_global
    chat_id_global = msg.chat.id

    try:
        domain = msg.text.split(" ")[1].lower()
        if domain not in domains:
            domains.append(domain)
            last_status[domain] = None
            bot.reply_to(msg, f"✅ Ditambahkan:\n{domain}")
        else:
            bot.reply_to(msg, "⚠ Sudah ada")
    except:
        bot.reply_to(msg, "Format: /add domain.com")

@bot.message_handler(commands=['check'])
def check_all(msg):
    global chat_id_global
    chat_id_global = msg.chat.id

    if not domains:
        bot.reply_to(msg, "⚠ Belum ada domain")
        return

    hasil = "✅ CHECK COMPLETED\n\n"
    hasil += f"📂 Total Domain: {len(domains)}\n"
    hasil += f"⏱ Time: {(datetime.utcnow().replace(hour=(datetime.utcnow().hour+7)%24)).strftime('%H:%M:%S')}\n\n"
    hasil += "📊 RESULTS:\n\n"

    safe = blocked = error = 0

    for d in domains:
        status = cek_nawala(d)

        if status == "safe":
            hasil += f"{d}  🟢\n"
            safe += 1
        elif status == "blocked":
            hasil += f"{d}  🔴\n"
            blocked += 1
        else:
            hasil += f"{d}  ⚠\n"
            error += 1

        last_status[d] = status

    hasil += "\n"
    hasil += f"🟢 Safe: {safe}\n"
    hasil += f"🔴 Blocked: {blocked}\n"
    hasil += f"⚠ Error: {error}"

    bot.reply_to(msg, hasil)

print("Bot jalan + auto monitor aktif...")
bot.infinity_polling()
