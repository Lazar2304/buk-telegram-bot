from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import os
import json
from dotenv import load_dotenv

# Učitavanje .env fajla
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# JSON fajl za čuvanje dugova
FILE = "dugovi.json"

def load_data():
    """Učitava podatke iz JSON fajla."""
    if not os.path.exists(FILE):
        return {}
    with open(FILE, "r") as f:
        return json.load(f)

def save_data(data):
    """Čuva podatke u JSON fajl."""
    with open(FILE, "w") as f:
        json.dump(data, f)

# --- Komande bota ---
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Zdravo! Ja sam zvanični bot BUK-a!\n\n"
        "Komande:\n"
        "/help - prikaži ovu poruku\n"
        "/dug <ime> <iznos> - dodaj dug članu\n"
        "/platio <ime> <iznos> - smanji dug članu\n"
        "/stanje - prikaz svih dugova"
    )

async def dug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()

    if len(context.args) != 2:
        await update.message.reply_text("Upotreba: /dug <ime> <iznos>")
        return

    ime = context.args[0]
    try:
        iznos = int(context.args[1])
    except ValueError:
        await update.message.reply_text("Iznos mora biti broj.")
        return

    if ime not in data:
        data[ime] = 0

    data[ime] += iznos
    save_data(data)
    await update.message.reply_text(f"{ime} sada duguje {data[ime]} dinara.")

async def platio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()

    if len(context.args) != 2:
        await update.message.reply_text("Upotreba: /platio <ime> <iznos>")
        return

    ime = context.args[0]
    try:
        iznos = int(context.args[1])
    except ValueError:
        await update.message.reply_text("Iznos mora biti broj.")
        return

    if ime not in data:
        await update.message.reply_text("Taj član ne postoji.")
        return

    data[ime] -= iznos
    save_data(data)
    await update.message.reply_text(f"{ime} sada duguje {data[ime]} dinara.")

async def stanje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()

    if not data:
        await update.message.reply_text("Nema dugovanja.")
        return

    tekst = "📊 Dugovanja:\n"
    for ime, dug in data.items():
        tekst += f"{ime}: {dug} din\n"

    await update.message.reply_text(tekst)

# --- Main ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Dodavanje komandi
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("dug", dug))
    app.add_handler(CommandHandler("platio", platio))
    app.add_handler(CommandHandler("stanje", stanje))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
