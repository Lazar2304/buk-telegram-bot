import os
import json
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Učitavanje .env fajla
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# JSON fajl za čuvanje dugova i budžeta
FILE = "dugovi.json"

def load_data():
    if not os.path.exists(FILE):
        initial_data = {"dugovi": {}, "budzet": 0}
        save_data(initial_data)
        return initial_data
    try:
        with open(FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"dugovi": {}, "budzet": 0}

def save_data(data):
    with open(FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- Komande bota ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        "📌 **Komande:**\n"
        "/dug <ime> <iznos> - dodaj dug članu\n"
        "/platio <ime> <iznos> - smanji dug i poveća budžet\n"
        "/stanje - prikaz svih dugova\n"
        "/budzet - prikaz ukupnog budžeta\n"
        "/obrisi <ime> - uklanja člana iz evidencije\n"
        "/help - prikaži ovu poruku"
    )

async def dug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Upotreba: /dug <ime> <iznos>")
        return
    
    ime = context.args[0]
    try:
        iznos = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Iznos mora biti ceo broj.")
        return

    data = load_data()
    data["dugovi"][ime] = data["dugovi"].get(ime, 0) + iznos
    save_data(data)
    
    await update.message.reply_text(f"✅ {ime} sada duguje {data['dugovi'][ime]} dinara.")

async def platio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Upotreba: /platio <ime> <iznos>")
        return

    ime = context.args[0]
    try:
        iznos_uplate = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Iznos mora biti ceo broj.")
        return

    data = load_data()
    if ime not in data["dugovi"]:
        await update.message.reply_text(f"❓ Član '{ime}' ne postoji u evidenciji.")
        return

    stari_dug = data["dugovi"][ime]
    # Smanjujemo dug, ali ne ispod 0
    novi_dug = max(0, stari_dug - iznos_uplate)
    data["dugovi"][ime] = novi_dug
    
    # Budžet raste za onoliko koliko je plaćeno
    data["budzet"] += iznos_uplate
    save_data(data)

    await update.message.reply_text(
        f"💰 {ime} je platio {iznos_uplate} din.\n"
        f"Preostali dug: {novi_dug} din.\n"
        f"Ukupan budžet: {data['budzet']} din."
    )

async def stanje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data["dugovi"] or all(v == 0 for v in data["dugovi"].values()):
        await update.message.reply_text("🎉 Nema aktivnih dugovanja!")
        return
    
    tekst = "📊 **Trenutna dugovanja:**\n"
    for ime, dug_iznos in data["dugovi"].items():
        if dug_iznos > 0:
            tekst += f"• {ime}: {dug_iznos} din\n"
    await update.message.reply_text(tekst)

async def budzet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    await update.message.reply_text(f"💰 **Trenutni budžet:** {data['budzet']} dinara.")

async def obrisi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Upotreba: /obrisi <ime>")
        return
    
    ime = context.args[0]
    data = load_data()
    if ime in data["dugovi"]:
        del data["dugovi"][ime]
        save_data(data)
        await update.message.reply_text(f"🗑️ Podaci za {ime} su obrisani.")
    else:
        await update.message.reply_text("❌ Taj član ne postoji.")

# --- Main ---
def main():
    if not BOT_TOKEN:
        print("Greška: BOT_TOKEN nije postavljen u .env fajlu!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("dug", dug))
    app.add_handler(CommandHandler("platio", platio))
    app.add_handler(CommandHandler("stanje", stanje))
    app.add_handler(CommandHandler("budzet", budzet))
    app.add_handler(CommandHandler("obrisi", obrisi))

    print("Bot je pokrenut...")
    app.run_polling()

if __name__ == "__main__":
    main()
