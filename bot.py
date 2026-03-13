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
    """Učitava podatke iz JSON fajla. Podržava UTF-8 za naša slova."""
    if not os.path.exists(FILE) or os.stat(FILE).st_size == 0:
        return {}
    try:
        with open(FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    """Čuva podatke u JSON fajl sa lepim formatiranjem."""
    with open(FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- Autocomplete i Inicijalizacija ---
async def post_init(application):
    """Ovo omogućava Autocomplete u Telegramu."""
    commands = [
        BotCommand("start", "Pokreni bota"),
        BotCommand("dug", "Dodaj dug: /dug ime iznos"),
        BotCommand("platio", "Smanji dug: /platio ime iznos"),
        BotCommand("stanje", "Prikaži sva dugovanja"),
        BotCommand("obrisi", "Obriši člana: /obrisi ime"),
        BotCommand("help", "Uputstvo")
    ]
    await application.bot.set_my_commands(commands)

# --- Komande bota ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prikazuje tastaturu sa dugmićima."""
    keyboard = [["/dug", "/platio"], ["/stanje", "/obrisi"], ["/help"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "👋 Zdravo! Ja sam zvanični bot BUK-a!\nIzaberi komandu ili kucaj `/`.",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 **Uputstvo:**\n\n"
        "/dug <ime> <iznos> - npr. `/dug Marko 500`\n"
        "/platio <ime> <iznos> - npr. `/platio Marko 200`\n"
        "/stanje - lista svih dugova\n"
        "/obrisi <ime> - briše člana iz baze",
        parse_mode="Markdown"
    )

async def dug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("⚠️ Upotreba: `/dug <ime> <iznos>`", parse_mode="Markdown")
        return

    ime = context.args[0]
    try:
        iznos = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Iznos mora biti broj.")
        return

    data = load_data()
    data[ime] = data.get(ime, 0) + iznos
    save_data(data)
    await update.message.reply_text(f"✅ {ime} sada duguje {data[ime]} dinara.")

async def platio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("⚠️ Upotreba: `/platio <ime> <iznos>`", parse_mode="Markdown")
        return

    ime = context.args[0]
    try:
        iznos = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Iznos mora biti broj.")
        return

    data = load_data()
    if ime not in data:
        await update.message.reply_text("❓ Taj član ne postoji u bazi.")
        return

    data[ime] = max(0, data[ime] - iznos)
    save_data(data)
    await update.message.reply_text(f"💰 {ime} je platio. Trenutni dug: {data[ime]} dinara.")

async def stanje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data or sum(data.values()) == 0:
        await update.message.reply_text("🎉 Nema aktivnih dugovanja.")
        return

    tekst = "📊 **Trenutna dugovanja:**\n"
    for ime, iznos in data.items():
        if iznos > 0:
            tekst += f"• {ime}: {iznos} din\n"
    await update.message.reply_text(tekst, parse_mode="Markdown")

async def obrisi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Upotreba: `/obrisi <ime>`", parse_mode="Markdown")
        return
    
    ime = context.args[0]
    data = load_data()
    if ime in data:
        del data[ime]
        save_data(data)
        await update.message.reply_text(f"🗑️ Član {ime} je obrisan.")
    else:
        await update.message.reply_text("❌ Član nije pronađen.")

# --- Main ---
def main():
    if not BOT_TOKEN:
        print("BOT_TOKEN nije setovan!")
        return

    # Ovde dodajemo post_init da aktiviramo autocomplete
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("dug", dug))
    app.add_handler(CommandHandler("platio", platio))
    app.add_handler(CommandHandler("stanje", stanje))
    app.add_handler(CommandHandler("obrisi", obrisi))

    print("Bot is running with autocomplete...")
    app.run_polling()

if __name__ == "__main__":
    main()
