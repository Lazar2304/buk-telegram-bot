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

async def get_target_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Vraća ime (string) iz argumenata ili ime pošiljaoca ako je unet samo iznos."""
    # 1. Ako je reply, uzmi ime te osobe
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        return f"{user.first_name} (@{user.username})" if user.username else user.first_name

    # 2. Ako ima 2 ili više argumenata (ime + iznos)
    if len(context.args) >= 2:
        # Uzmi sve osim poslednjeg elementa (iznosa) kao ime
        return " ".join(context.args[:-1])

    # 3. Ako ima samo 1 argument (pretpostavljamo da je to iznos za samog sebe)
    if len(context.args) == 1:
        try:
            int(context.args[0])
            user = update.message.from_user
            return f"{user.first_name} (@{user.username})" if user.username else user.first_name
        except ValueError:
            return context.args[0] # Ako nije broj, tretiraj kao ime bez iznosa (prijaviće grešku kasnije)

    return None

# --- Autocomplete ---
async def post_init(application):
    await application.bot.set_my_commands([
        BotCommand("start", "Pokreni bota"),
        BotCommand("dug", "Dodaj dug: /dug ime iznos"),
        BotCommand("platio", "Smanji dug i poveća budžet"),
        BotCommand("kasnjenje", "Dodaj minute: /kasnjenje ime minuti"),
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
        "/dug <ime> <iznos> - dodaj dug članu\n"
        "/platio <ime> <iznos> - smanji dug članu i povećaj budžet\n"
        "/kasnjenje <ime> <minuti> - dodaj minute i automatski dug (5din/min)\n"
        "/stanje - prikaz svih dugova i ukupnog kašnjenja\n"
        "/budzet - prikaz trenutnog budžeta\n"
        "/smanji_budzet <iznos> - trošenje novca iz budžeta\n"
        "/obrisi <ime> - briše člana iz baze"
    )

async def dug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ime = await get_target_name(update, context)
    try:
        iznos = int(context.args[-1])
    except (ValueError, IndexError):
        await update.message.reply_text("Upotreba: /dug <ime> <iznos>")
        return

    chat_id = update.effective_chat.id
    all_data = load_data()
    data = get_chat_data(all_data, chat_id)
    data["dugovi"][ime] = data["dugovi"].get(ime, 0) + iznos
    save_data(all_data)
    await update.message.reply_text(f"{ime} sada duguje {data['dugovi'][ime]} dinara.")

async def platio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ime = await get_target_name(update, context)
    try:
        iznos = int(context.args[-1])
    except (ValueError, IndexError):
        await update.message.reply_text("Upotreba: /platio <ime> <iznos>")
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
    ime = await get_target_name(update, context)
    try:
        minuti = int(context.args[-1])
    except (ValueError, IndexError):
        await update.message.reply_text("Upotreba: /kasnjenje <ime> <minuti>")
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
    if not context.args:
        ime = f"{update.message.from_user.first_name} (@{update.message.from_user.username})" if update.message.from_user.username else update.message.from_user.first_name
    else:
        ime = " ".join(context.args)

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
