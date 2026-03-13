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
    if not os.path.exists(FILE) or os.stat(FILE).st_size == 0:
        return {}
    try:
        with open(FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_chat_data(all_data, chat_id):
    cid = str(chat_id)
    if cid not in all_data:
        all_data[cid] = {"dugovi": {}, "kasnjenja": {}, "budzet": 0}
    return all_data[cid]

async def get_valid_user(update: Update):
    """Vraća ime i prezime korisnika samo ako je @mention ili Reply."""
    target_user = None
    
    # 1. Provera preko Reply-a
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    # 2. Provera preko Mention-a u poruci
    elif update.message.entities:
        for entity in update.message.entities:
            if entity.type == "mention":
                # Izvlačimo korisnika iz mention-a (ovo radi samo ako je korisnik u grupi)
                mention_text = update.message.text[entity.offset:entity.offset+entity.length]
                # Napomena: Bot ne može uvek da dobije UserID samo iz @username teksta 
                # osim ako korisnik nije tagovan. Zato koristimo tagovan tekst kao ključ.
                return mention_text

    if target_user:
        return f"{target_user.first_name} (@{target_user.username})" if target_user.username else target_user.first_name
    return None

# --- Autocomplete ---
async def post_init(application):
    # Postavljanje komandi bez sufiksa username-a bota
    await application.bot.set_my_commands([
        BotCommand("start", "Pokreni bota"),
        BotCommand("dug", "Dodaj dug: /dug @korisnik iznos"),
        BotCommand("platio", "Smanji dug i poveća budžet"),
        BotCommand("kasnjenje", "Dodaj minute: /kasnjenje @korisnik minuti"),
        BotCommand("stanje", "Prikaži sva dugovanja i kasnjenja"),
        BotCommand("budzet", "Prikaži budžet"),
        BotCommand("smanji_budzet", "Trošenje iz budžeta: /smanji_budzet iznos"),
        BotCommand("obrisi", "Obriši člana"),
        BotCommand("help", "Uputstvo")
    ])

# --- Komande bota ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["/dug", "/platio"], ["/kasnjenje", "/stanje"], ["/budzet", "/smanji_budzet"], ["/help"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("👋 StaljinBot spreman!", reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Zdravo! Ja sam zvanični bot BUK-a!\n\n"
        "Komande:\n"
        "/help - prikaži ovu poruku\n"
        "/dug <@korisnik> <iznos> - dodaj dug članu\n"
        "/platio <@korisnik> <iznos> - smanji dug članu i povećaj budžet\n"
        "/kasnjenje <@korisnik> <minuti> - dodaj minute i automatski dug (5din/min)\n"
        "/stanje - prikaz svih dugova i ukupnog kašnjenja\n"
        "/budzet - prikaz trenutnog budžeta\n"
        "/smanji_budzet <iznos> - trošenje novca iz budžeta\n"
        "/obrisi <@korisnik> - briše člana iz baze"
    )

async def dug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ime = await get_valid_user(update)
    if not ime:
        await update.message.reply_text("Upotreba: /dug <@korisnik> <iznos> (ili reply na poruku)")
        return
    
    try:
        # Uzimamo poslednji argument kao iznos
        iznos = int(context.args[-1])
    except (ValueError, IndexError):
        await update.message.reply_text("Iznos mora biti broj.")
        return

    chat_id = update.effective_chat.id
    all_data = load_data()
    data = get_chat_data(all_data, chat_id)
    data["dugovi"][ime] = data["dugovi"].get(ime, 0) + iznos
    save_data(all_data)
    await update.message.reply_text(f"{ime} sada duguje {data['dugovi'][ime]} dinara.")

async def platio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ime = await get_valid_user(update)
    if not ime:
        await update.message.reply_text("Upotreba: /platio <@korisnik> <iznos>")
        return
    
    try:
        iznos = int(context.args[-1])
    except (ValueError, IndexError):
        await update.message.reply_text("Iznos mora biti broj.")
        return

    chat_id = update.effective_chat.id
    all_data = load_data()
    data = get_chat_data(all_data, chat_id)
    if ime in data["dugovi"]:
        data["dugovi"][ime] = max(0, data["dugovi"][ime] - iznos)
        data["budzet"] += iznos
        save_data(all_data)
        await update.message.reply_text(f"{ime} sada duguje {data['dugovi'][ime]} dinara.\nUkupan budžet: {data['budzet']} dinara.")
    else:
        await update.message.reply_text("Taj član ne postoji.")

async def kasnjenje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ime = await get_valid_user(update)
    if not ime:
        await update.message.reply_text("Upotreba: /kasnjenje <@korisnik> <minuti>")
        return
    
    try:
        minuti = int(context.args[-1])
    except (ValueError, IndexError):
        await update.message.reply_text("Minuti moraju biti broj.")
        return

    kazna = minuti * 5
    chat_id = update.effective_chat.id
    all_data = load_data()
    data = get_chat_data(all_data, chat_id)
    data["kasnjenja"][ime] = data["kasnjenja"].get(ime, 0) + minuti
    data["dugovi"][ime] = data["dugovi"].get(ime, 0) + kazna
    save_data(all_data)
    await update.message.reply_text(f"{ime} sada duguje {data['dugovi'][ime]} dinara.")

async def stanje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    all_data = load_data()
    data = get_chat_data(all_data, chat_id)
    svi_clanova = set(list(data["dugovi"].keys()) + list(data["kasnjenja"].keys()))
    if not svi_clanova:
        await update.message.reply_text("Nema dugovanja.")
        return
    tekst = "📊 Dugovanja:\n"
    for ime in svi_clanova:
        d = data["dugovi"].get(ime, 0)
        k = data["kasnjenja"].get(ime, 0)
        tekst += f"{ime}: {d} din (Ukupno kašnjenje: {k} min)\n"
    await update.message.reply_text(tekst)

async def budzet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    all_data = load_data()
    data = get_chat_data(all_data, chat_id)
    await update.message.reply_text(f"💰 Trenutni budžet: {data['budzet']} dinara.")

async def smanji_budzet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Upotreba: /smanji_budzet <iznos>")
        return
    try:
        iznos = int(context.args[0])
    except:
        await update.message.reply_text("Iznos mora biti broj.")
        return
    chat_id = update.effective_chat.id
    all_data = load_data()
    data = get_chat_data(all_data, chat_id)
    data["budzet"] = max(0, data["budzet"] - iznos)
    save_data(all_data)
    await update.message.reply_text(f"Budžet smanjen za {iznos}. Trenutno stanje: {data['budzet']} dinara.")

async def obrisi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ime = await get_valid_user(update)
    if not ime:
        await update.message.reply_text("Upotreba: /obrisi <@korisnik>")
        return
    chat_id = update.effective_chat.id
    all_data = load_data()
    data = get_chat_data(all_data, chat_id)
    if ime in data["dugovi"]: del data["dugovi"][ime]
    if ime in data["kasnjenja"]: del data["kasnjenja"][ime]
    save_data(all_data)
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
