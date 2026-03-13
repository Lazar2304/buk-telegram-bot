import os
import json
import logging
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Logovanje grešaka u konzoli (važno da vidiš ako nešto pukne)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
FILE = "dugovi.json"

# --- Rad sa podacima ---
def load_data():
    if not os.path.exists(FILE) or os.stat(FILE).st_size == 0:
        data = {"dugovi": {}, "budzet": 0}
        save_data(data)
        return data
    try:
        with open(FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Greška pri čitanju fajla: {e}")
        return {"dugovi": {}, "budzet": 0}

def save_data(data):
    with open(FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- Komande bota ---
async def post_init(application):
    """Ova funkcija postavlja autocomplete komande u Telegramu"""
    commands = [
        BotCommand("start", "Pokreni bota"),
        BotCommand("dug", "Dodaj dug: /dug ime iznos"),
        BotCommand("platio", "Zabeleži uplatu: /platio ime iznos"),
        BotCommand("stanje", "Prikaži sva dugovanja"),
        BotCommand("budzet", "Prikaži trenutni budžet"),
        BotCommand("obrisi", "Obriši člana: /obrisi ime"),
        BotCommand("help", "Pomoć i uputstva")
    ]
    await application.bot.set_my_commands(commands)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["/dug", "/platio"],
        ["/stanje", "/budzet"],
        ["/obrisi", "/help"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "👋 Zdravo! Ja sam BUK dug-bot.\nKucaj / ili koristi dugmad ispod.",
        reply_markup=reply_markup
    )

async def dug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Upotreba: `/dug ime iznos` (npr. /dug Marko 500)", parse_mode="Markdown")
        return
    
    ime = context.args[0]
    try:
        iznos = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Iznos mora biti ceo broj!")
        return

    data = load_data()
    data["dugovi"][ime] = data["dugovi"].get(ime, 0) + iznos
    save_data(data)
    await update.message.reply_text(f"✅ Dodato! {ime} sada duguje {data['dugovi'][ime]} din.")

async def platio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Upotreba: `/platio ime iznos`", parse_mode="Markdown")
        return

    ime = context.args[0]
    try:
        iznos = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Iznos mora biti broj!")
        return

    data = load_data()
    if ime not in data["dugovi"]:
        await update.message.reply_text(f"❓ Član '{ime}' ne postoji.")
        return

    data["dugovi"][ime] = max(0, data["dugovi"][ime] - iznos)
    data["budzet"] += iznos
    save_data(data)
    await update.message.reply_text(f"💰 {ime} je uplatio {iznos} din.\nStanje duga: {data['dugovi'][ime]} din.\nBudžet: {data['budzet']} din.")

async def stanje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    dugovi = data.get("dugovi", {})
    if not dugovi or sum(dugovi.values()) == 0:
        await update.message.reply_text("🎉 Niko ništa ne duguje!")
        return
    
    izvestaj = "📊 **Trenutni dugovi:**\n"
    for ime, iznos in dugovi.items():
        if iznos > 0:
            izvestaj += f"• {ime}: {iznos} din\n"
    await update.message.reply_text(izvestaj, parse_mode="Markdown")

async def budzet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    await update.message.reply_text(f"💰 Trenutni budžet BUK-a je: **{data['budzet']}** dinara.", parse_mode="Markdown")

async def obrisi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Upotreba: `/obrisi ime`", parse_mode="Markdown")
        return
    
    ime = context.args[0]
    data = load_data()
    if ime in data["dugovi"]:
        del data["dugovi"][ime]
        save_data(data)
        await update.message.reply_text(f"🗑️ {ime} je obrisan iz baze.")
    else:
        await update.message.reply_text("❌ Član nije pronađen.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Uputstvo:\n/dug <ime> <iznos>\n/platio <ime> <iznos>\n/stanje\n/budzet\n/obrisi <ime>")

# --- Glavna funkcija ---
def main():
    if not BOT_TOKEN:
        print("❌ GREŠKA: BOT_TOKEN nije pronađen u .env fajlu!")
        return

    # Dodajemo post_init da podesimo komande pri pokretanju
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("dug", dug))
    app.add_handler(CommandHandler("platio", platio))
    app.add_handler(CommandHandler("stanje", stanje))
    app.add_handler(CommandHandler("budzet", budzet))
    app.add_handler(CommandHandler("obrisi", obrisi))

    print("🚀 Bot je pokrenut i autocomplete je spreman!")
    app.run_polling()

if __name__ == "__main__":
    main()
