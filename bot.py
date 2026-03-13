import os
import json
import logging
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Osnovno logovanje
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
FILE = "dugovi.json"

# --- Rad sa podacima ---
def load_data():
    default_data = {"dugovi": {}, "kasnjenja": {}, "budzet": 0}
    if not os.path.exists(FILE) or os.stat(FILE).st_size == 0:
        return default_data
    try:
        with open(FILE, "r", encoding='utf-8') as f:
            data = json.load(f)
            if "dugovi" not in data:
                return {"dugovi": data, "kasnjenja": {}, "budzet": 0}
            return data
    except:
        return default_data

def save_data(data):
    with open(FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- Autocomplete ---
async def post_init(application):
    commands = [
        BotCommand("start", "Pokreni bota"),
        BotCommand("dug", "Dodaj dug: /dug ime iznos"),
        BotCommand("platio", "Smanji dug i poveća budžet"),
        BotCommand("kasnjenje", "Dodaj minute: /kasnjenje ime minuti"),
        BotCommand("stanje", "Prikaži sva dugovanja i kasnjenja"),
        BotCommand("budzet", "Prikaži budžet"),
        BotCommand("smanji_budzet", "Trošenje iz budžeta: /smanji_budzet iznos"),
        BotCommand("obrisi", "Obriši člana"),
        BotCommand("help", "Uputstvo")
    ]
    await application.bot.set_my_commands(commands)

# --- Komande bota ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["/dug", "/platio"], ["/kasnjenje", "/stanje"], ["/budzet", "/smanji_budzet"], ["/help"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("👋 Bot BUK-a spreman!", reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Zdravo! Ja sam zvanični bot BUK-a!\n\n"
        "Komande:\n"
        "/help - prikaži ovu poruku\n"
        "/dug <ime> <iznos> - dodaj dug članu\n"
        "/platio <ime> <iznos> - smanji dug članu i povećaj budžet\n"
        "/kasnjenje <ime> <minuti> - dodaj minute i automatski dug (5din/min)\n"
        "/stanje - prikaz svih dugova i ukupnog kašnjenja\n"
        "/budzet - prikaz trenutnog budžeta\n"
        "/smanji_budzet <iznos> - trošenje novca iz budžeta\n"
        "/obrisi <ime> - briše člana iz baze"
    )

async def dug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Upotreba: /dug <ime> <iznos>")
        return
    ime, iznos = context.args[0], int(context.args[1])
    data = load_data()
    data["dugovi"][ime] = data["dugovi"].get(ime, 0) + iznos
    save_data(data)
    await update.message.reply_text(f"{ime} sada duguje {data['dugovi'][ime]} dinara.")

async def platio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Upotreba: /platio <ime> <iznos>")
        return
    ime, iznos = context.args[0], int(context.args[1])
    data = load_data()
    if ime in data["dugovi"]:
        data["dugovi"][ime] = max(0, data["dugovi"][ime] - iznos)
        data["budzet"] += iznos
        save_data(data)
        await update.message.reply_text(f"{ime} sada duguje {data['dugovi'][ime]} dinara.\nUkupan budžet: {data['budzet']} dinara.")
    else:
        await update.message.reply_text("Taj član ne postoji.")

async def kasnjenje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Upotreba: /kasnjenje <ime> <minuti>")
        return
    ime = context.args[0]
    minuti = int(context.args[1])
    kazna = minuti * 5
    data = load_data()
    data["kasnjenja"][ime] = data["kasnjenja"].get(ime, 0) + minuti
    data["dugovi"][ime] = data["dugovi"].get(ime, 0) + kazna
    save_data(data)
    await update.message.reply_text(f"{ime} sada duguje {data['dugovi'][ime]} dinara.")

async def stanje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    svi_clanova = set(list(data["dugovi"].keys()) + list(data["kasnjenja"].keys()))
    if not svi_clanova:
        await update.message.reply_text("Nema dugovanja.")
        return
    tekst = "📊 Dugovanja:\n"
    for ime in svi_clanova:
        d = data["dugovi"].get(ime, 0)
        k = data["kasnjenja"].get(ime, 0)
        tekst += f"{ime}: {d} din (Ukupno kasnjenje: {k} min)\n"
    await update.message.reply_text(tekst)

async def budzet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    await update.message.reply_text(f"💰 Trenutni budžet: {data['budzet']} dinara.")

async def smanji_budzet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Upotreba: /smanji_budzet <iznos>")
        return
    try:
        iznos = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Iznos mora biti broj.")
        return
    data = load_data()
    data["budzet"] = max(0, data["budzet"] - iznos)
    save_data(data)
    await update.message.reply_text(f"Budžet smanjen za {iznos}. Trenutno stanje: {data['budzet']} dinara.")

async def obrisi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Upotreba: /obrisi <ime>")
        return
    ime = context.args[0]
    data = load_data()
    if ime in data["dugovi"]: del data["dugovi"][ime]
    if ime in data["kasnjenja"]: del data["kasnjenja"][ime]
    save_data(data)
    await update.message.reply_text(f"Dug {ime} je obrisan bez dodavanja u budžet.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("dug", dug))
    app.add_handler(CommandHandler("platio", platio))
    app.add_handler(CommandHandler("kasnjenje", kasnjenje))
    app.add_handler(CommandHandler("stanje", stanje))
    app.add_handler(CommandHandler("budzet", budzet))
    app.add_handler(CommandHandler("smanji_budzet", smanji_budzet))
    app.add_handler(CommandHandler("obrisi", obrisi))
    app.run_polling()

if __name__ == "__main__":
    main()
