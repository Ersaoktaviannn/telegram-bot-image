# -*- coding: utf-8 -*-
"""DailyBot

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1KfVb7KDaRrVU80b7RLPixIvm9fJpj9ES
"""

import os
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Simpan TOKEN di environment variable atau file terpisah
TOKEN = '7755128544:AAES3q1UQZaR83h1-m0H_cejTeps0WN_2lA'

def start(update, context):
    """Handler untuk perintah /start"""
    chat_id = update.effective_chat.id
    nama_pengguna = update.effective_user.first_name

    # Pesan selamat datang
    welcome_message = (
        f"Halo {nama_pengguna}! 👋\n"
        "Selamat datang di bot reporting otomatis.\n"
        "Bot ini akan membantu Anda melacak status tugas."
    )

    context.bot.send_message(
        chat_id=chat_id,
        text=welcome_message
    )

def setup_bot():
    """Fungsi untuk menyiapkan bot"""
    # Inisialisasi updater dan dispatcher
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Tambahkan handler untuk perintah /start
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    # Jalankan bot
    updater.start_polling()
    print("Bot berhasil dimulai!")

    # Jalankan bot hingga dihentikan
    updater.idle()

if __name__ == '__main__':
    setup_bot()