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
    """Učitava podatke. Ako je fajl starog formata ili ne postoji, inicijalizuje novi format."""
    default_data = {"dugovi": {}, "kasnjenja": {}, "budzet": 0}
    if not os.path.exists(FILE) or os.stat(FILE).st_size == 0:
        return default_data
    try:
        with open(FILE, "r", encoding='utf-8') as f:
            data = json.load(f)
            # Osiguravamo da novi ključevi postoje ako prelazimo sa stare verzije
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
        BotCommand("platio", "Smanji dug i povećaj budžet"),
        BotCommand("kasnjenje", "Dodaj minute: /kasnjenje ime minuti"),
        BotCommand("stanje", "Prikaži sva dugovanja i kasnjenja"),
        BotCommand("budzet", "Prikaži ukupni budžet"),
        BotCommand("obrisi", "Obriši člana"),
        BotCommand("help", "Uputstvo")
    ]
    await application.bot.set_my_commands(commands)

# --- Komande bota ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["/dug", "/platio"], ["/kasnjenje", "/stanje"], ["/budzet", "/help"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("👋 Bot BUK-a spreman!", reply_markup=reply_markup)

async def dug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("⚠️ Upotreba: `/dug <ime> <iznos>`", parse_mode="Markdown")
        return
    ime, iznos = context.args[0], int(context.args[1])
    data = load_data()
    data["dugovi"][ime] = data["dugovi"].get(ime, 0) + iznos
    save_data(data)
    await update.message.reply_text(f"✅ {ime} sada duguje {data['dugovi'][ime]} din.")

async def platio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("⚠️ Upotreba: `/platio <ime> <iznos>`", parse_mode="Markdown")
        return
    ime, iznos = context.args[0], int(context.args[1])
    data = load_data()
    if ime in data["dugovi"]:
        stari_dug = data["dugovi"][ime]
        data["dugovi"][ime] = max(0, stari_dug - iznos)
        data["budzet"] += iznos  # Povećava budžet
        save_data(data)
        await update.message.reply_text(f"💰 Uplata proknjižena! Novi dug: {data['dugovi'][ime]} din. Budžet: {data['budzet']} din.")
    else:
        await update.message.reply_text("❌ Član ne postoji.")

async def kasnjenje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("⚠️ Upotreba: `/kasnjenje <ime> <minuti>`", parse_mode="Markdown")
        return
    ime = context.args[0]
    try:
        minuti = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Minuti moraju biti broj.")
        return

    kazna = minuti * 5  # 5 dinara po minutu
    data = load_data()
    
    # Dodajemo minute u listu kasnjenja
    data["kasnjenja"][ime] = data["kasnjenja"].get(ime, 0) + minuti
    # Automatski dodajemo iznos kazne u dugovanja
    data["dugovi"][ime] = data["dugovi"].get(ime, 0) + kazna
    
    save_data(data)
    await update.message.reply_text(
        f"⏳ Zabeleženo: {ime} kasni {minuti} min.\n"
        f"Dug mu je uvećan za {kazna} din (ukupni dug: {data['dugovi'][ime]} din)."
    )

async def stanje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    tekst = "📊 **Trenutni presek:**\n\n"
    
    svi_clanova = set(list(data["dugovi"].keys()) + list(data["kasnjenja"].keys()))
    if not svi_clanova:
        await update.message.reply_text("🎉 Nema podataka u bazi.")
        return

    for ime in svi_clanova:
        d = data["dugovi"].get(ime, 0)
        k = data["kasnjenja"].get(ime, 0)
        tekst += f"👤 **{ime}**\n   • Dug: {d} din\n   • Kasnjenje: {k} min\n"
    
    await update.message.reply_text(tekst, parse_mode="Markdown")

async def budzet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    await update.message.reply_text(f"💰 **Ukupan budžet BUK-a:** {data['budzet']} dinara.", parse_mode="Markdown")

async def obrisi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Upotreba: `/obrisi <ime>`", parse_mode="Markdown")
        return
    ime = context.args[0]
    data = load_data()
    if ime in data["dugovi"]: del data["dugovi"][ime]
    if ime in data["kasnjenja"]: del data["kasnjenja"][ime]
    save_data(data)
    await update.message.reply_text(f"🗑️ Podaci za {ime} su obrisani.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("dug", dug))
    app.add_handler(CommandHandler("platio", platio))
    app.add_handler(CommandHandler("kasnjenje", kasnjenje))
    app.add_handler(CommandHandler("stanje", stanje))
    app.add_handler(CommandHandler("budzet", budzet))
    app.add_handler(CommandHandler("obrisi", obrisi))
    app.run_polling()

if __name__ == "__main__":
    main()
