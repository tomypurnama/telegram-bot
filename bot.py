import telebot
import os
import dns.resolver
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# simpan domain (sementara di memory)
domains = []

NAWALA_DNS = ["180.131.144.144", "180.131.145.145"]

def cek_nawala(domain):
    resolver = dns.resolver.Resolver()
    resolver.nameservers = NAWALA_DNS

    try:
        answer = resolver.resolve(domain, "A")
        ips = [rdata.to_text() for rdata in answer]
        return "safe", ips
    except dns.resolver.NXDOMAIN:
        return "blocked", None
    except:
        return "error", None

# ================= COMMAND ================= #

@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(msg, "🤖 BOT NAWALA READY\n\n/add domain.com\n/del domain.com\n/check")

@bot.message_handler(commands=['add'])
def add_domain(msg):
    try:
        domain = msg.text.split(" ")[1].lower()
        if domain not in domains:
            domains.append(domain)
            bot.reply_to(msg, f"✅ Ditambahkan:\n{domain}")
        else:
            bot.reply_to(msg, "⚠ Sudah ada")
    except:
        bot.reply_to(msg, "Format: /add domain.com")

@bot.message_handler(commands=['del'])
def del_domain(msg):
    try:
        domain = msg.text.split(" ")[1].lower()
        if domain in domains:
            domains.remove(domain)
            bot.reply_to(msg, f"❌ Dihapus:\n{domain}")
        else:
            bot.reply_to(msg, "⚠ Tidak ditemukan")
    except:
        bot.reply_to(msg, "Format: /del domain.com")

@bot.message_handler(commands=['check'])
def check_all(msg):
    if not domains:
        bot.reply_to(msg, "⚠ Belum ada domain")
        return

    hasil = "✅ CHECK COMPLETED\n\n"
    hasil += f"📂 Total Domain: {len(domains)}\n"
    hasil += f"⏱ Time: {datetime.now().strftime('%H:%M:%S')}\n\n"
    hasil += "📊 RESULTS:\n\n"

    safe = 0
    blocked = 0
    error = 0

    for d in domains:
        status, _ = cek_nawala(d)

        if status == "safe":
            hasil += f"{d}  🟢\n"
            safe += 1
        elif status == "blocked":
            hasil += f"{d}  🔴\n"
            blocked += 1
        else:
            hasil += f"{d}  ⚠\n"
            error += 1

    hasil += "\n"
    hasil += f"🟢 Safe: {safe}\n"
    hasil += f"🔴 Blocked: {blocked}\n"
    hasil += f"⚠ Error: {error}"

    bot.reply_to(msg, hasil)

print("Bot jalan...")
bot.infinity_polling()
