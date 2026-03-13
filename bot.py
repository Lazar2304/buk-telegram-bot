from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import os
import json
from dotenv import load_dotenv

# Učitavanje .env fajla
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# JSON fajl za čuvanje dugova i budžeta
FILE = "dugovi.json"

def load_data():
    if not os.path.exists(FILE):
        # kreira bazu samo ako fajl ne postoji
        return {"dugovi": {}, "budzet": 0}
    with open(FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(FILE, "w") as f:
        json.dump(data, f)

# --- Komande bota ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Dugmad za komande
    keyboard = [
        ["/dug", "/platio"],
        ["/stanje", "/budzet"],
        ["/obrisi", "/help"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Zdravo! Ja sam zvanični bot BUK-a!\nIzaberi komandu dugmetom ili kucaj ručno.",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Komande:\n"
        "/dug <ime> <iznos> - dodaj dug članu\n"
        "/platio <ime> <iznos> - smanji dug članu i poveća budžet\n"
        "/stanje - prikaz svih dugova\n"
        "/budzet - prikaz ukupnog budžeta\n"
        "/obrisi <ime> - uklanja dug člana bez dodavanja u budžet\n"
        "/help - prikaži ovu poruku"
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

    if ime not in data["dugovi"]:
        data["dugovi"][ime] = 0

    data["dugovi"][ime] += iznos
    save_data(data)
    await update.message.reply_text(f"{ime} sada duguje {data['dugovi'][ime]} dinara.")

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

    if ime not in data["dugovi"]:
        await update.message.reply_text("Taj član ne postoji.")
        return

    data["dugovi"][ime] -= iznos
    if data["dugovi"][ime] < 0:
        data["dugovi"][ime] = 0

    data["budzet"] += iznos  # plaćanjem se povećava budžet
    save_data(data)
    await update.message.reply_text(
        f"{ime} sada duguje {data['dugovi'][ime]} dinara.\n"
        f"Ukupan budžet: {data['budzet']} dinara."
    )

async def stanje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data["dugovi"]:
        await update.message.reply_text("Nema dugovanja.")
        return
    tekst = "📊 Dugovanja:\n"
    for ime, dug in data["dugovi"].items():
        tekst += f"{ime}: {dug} din\n"
    await update.message.reply_text(tekst)

async def budzet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    await update.message.reply_text(f"💰 Trenutni budžet: {data['budzet']} dinara.")

async def obrisi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if len(context.args) != 1:
        await update.message.reply_text("Upotreba: /obrisi <ime>")
        return
    ime = context.args[0]
    if ime in data["dugovi"]:
        data["dugovi"].pop(ime)
        save_data(data)
        await update.message.reply_text(f"Dug {ime} je obrisan bez dodavanja u budžet.")
    else:
        await update.message.reply_text("Taj član ne postoji.")

# --- Main ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("dug", dug))
    app.add_handler(CommandHandler("platio", platio))
    app.add_handler(CommandHandler("stanje", stanje))
    app.add_handler(CommandHandler("budzet", budzet))
    app.add_handler(CommandHandler("obrisi", obrisi))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
