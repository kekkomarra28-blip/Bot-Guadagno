import os
import asyncio
import logging
from datetime import datetime
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import feedparser
import httpx
from bs4 import BeautifulSoup

TOKEN = "AAFXGHcJxmK68UdCjh8gyjhMu1VtcCUm8ws"
CHAT_ID = "8893690358"
ORARIO_INVIO = "09:00"

FONTI_RSS = {
    "💰 Cashback & Risparmio": [
        "https://www.cashbackdeals.it/feed/",
        "https://www.groupon.it/rss",
        "https://feeds.feedburner.com/Pirateinformatico",
    ],
    "📱 App & Siti di Guadagno": [
        "https://www.guadagnareonline.it/feed/",
        "https://www.lavoroalternativi.com/feed/",
        "https://www.money.it/RSS-money.xml",
    ],
    "💼 Lavori Freelance": [
        "https://freelancermap.it/rss.xml",
    ],
    "🎁 Offerte & Promozioni": [
        "https://www.hwupgrade.it/news/rss.xml",
        "https://www.smartworld.it/feed",
    ],
}

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_rss_feed(url, max_items=3):
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            feed = feedparser.parse(resp.text)
            items = []
            for entry in feed.entries[:max_items]:
                items.append({
                    "titolo": entry.get("title", "Nessun titolo")[:100],
                    "link": entry.get("link", ""),
                })
            return items
    except Exception as e:
        logger.warning(f"Errore feed {url}: {e}")
        return []

async def raccogli_tutte_offerte():
    risultati = {}
    for categoria, urls in FONTI_RSS.items():
        offerte = []
        for url in urls:
            items = await fetch_rss_feed(url)
            offerte.extend(items)
        if offerte:
            risultati[categoria] = offerte[:6]
    return risultati

def formatta_messaggio(offerte):
    ora = datetime.now().strftime("%d/%m/%Y %H:%M")
    messaggi = []
    intro = f"🤖 *OFFERTE GUADAGNO ONLINE*\n📅 {ora}\n{'─'*30}\n\n"
    blocco = intro
    for categoria, items in offerte.items():
        sezione = f"\n{categoria}\n"
        for i, item in enumerate(items, 1):
            sezione += f"{i}. [{item['titolo']}]({item['link']})\n"
        sezione += "\n"
        if len(blocco) + len(sezione) > 4000:
            messaggi.append(blocco)
            blocco = sezione
        else:
            blocco += sezione
    if blocco.strip():
        messaggi.append(blocco)
    return messaggi or ["⚠️ Nessuna offerta trovata al momento."]

async def start(update, context):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"👋 *Ciao! Sono il tuo Bot Offerte Guadagno!*\n\n"
        f"🆔 Il tuo Chat ID è: `{chat_id}`\n\n"
        f"/offerte — Tutte le offerte\n"
        f"/cashback — Solo cashback\n"
        f"/freelance — Solo freelance\n"
        f"/app — Solo app guadagno\n\n"
        f"⏰ Aggiornamento automatico ogni 24 ore!",
        parse_mode="Markdown"
    )

async def cmd_offerte(update, context):
    await update.message.reply_text("⏳ Sto cercando le offerte...")
    offerte = await raccogli_tutte_offerte()
    for msg in formatta_messaggio(offerte):
        await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)

async def cmd_cashback(update, context):
    await update.message.reply_text("⏳ Cerco offerte cashback...")
    offerte = {k: v for k, v in (await raccogli_tutte_offerte()).items() if "Cashback" in k}
    for msg in formatta_messaggio(offerte):
        await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)

async def cmd_freelance(update, context):
    await update.message.reply_text("⏳ Cerco lavori freelance...")
    offerte = {k: v for k, v in (await raccogli_tutte_offerte()).items() if "Freelance" in k}
    for msg in formatta_messaggio(offerte):
        await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)

async def cmd_app(update, context):
    await update.message.reply_text("⏳ Cerco app e siti di guadagno...")
    offerte = {k: v for k, v in (await raccogli_tutte_offerte()).items() if "App" in k}
    for msg in formatta_messaggio(offerte):
        await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)

async def invia_automatico(context):
    offerte = await raccogli_tutte_offerte()
    for msg in formatta_messaggio(offerte):
        await context.bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown", disable_web_page_preview=True)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("offerte", cmd_offerte))
    app.add_handler(CommandHandler("cashback", cmd_cashback))
    app.add_handler(CommandHandler("freelance", cmd_freelance))
    app.add_handler(CommandHandler("app", cmd_app))
    app.job_queue.run_repeating(invia_automatico, interval=86400, first=10)
    print("🚀 Bot avviato!")
    app.run_polling()

if __name__ == "__main__":
    main()