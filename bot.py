import telebot
import os

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(func=lambda message: True)
def reply(message):
    bot.reply_to(message, "Halo! Bot aktif 🚀")

bot.infinity_polling()