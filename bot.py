from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import os
from dotenv import load_dotenv

load_dotenv()  # load .env file
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Zdravo! Ja sam zvanični bot BUK-a!")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("help", help_command))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
