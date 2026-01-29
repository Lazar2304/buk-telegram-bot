from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = "8324420046:AAGfOcS504H4ZtPU0B2TwRITM0hiTwWj2_8"

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Zdravo! Ja sam zvanični bot BUK-a!")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("help", help_command))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
