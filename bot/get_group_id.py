from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler

TOKEN = "7755128544:AAES3q1UQZaR83h1-m0H_cejTeps0WN_2lA"

async def get_chat_id(update: Update, context):
    chat_id = update.message.chat_id
    await update.message.reply_text(f"ID Grup ini: {chat_id}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("getid", get_chat_id))
    print("Bot sedang berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
