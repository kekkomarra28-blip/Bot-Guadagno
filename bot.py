import os
import logging
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import feedparser
import httpx

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

FONTI_RSS = {
    "💰 Cashback & Risparmio": [
        "https://feeds.feedburner.com/Pirateinformatico",
        "https://www.groupon.it/rss",
    ],
    "📱 App & Siti di Guadagno": [
        "https://www.money.it/RSS-money.xml",
        "https://www.smartworld.it/feed",
    ],
    "💼 Lavori Freelance": [
        "https://freelancermap.it/rss.xml",
    ],
    "🎁 Offerte & Promozioni": [
        "https://www.hwupgrade.it/news/rss.xml",
    ],
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_feed(url, max_items=3):
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            feed = feedparser.parse(resp.text)
            return [{"titolo": e.get("title","")[:100], "link": e.get("link","")} for e in feed.entries[:max_items]]
    except:
        return []

async def raccogli():
    risultati = {}
    for cat, urls in FONTI_RSS.items():
        items = []
        for url in urls:
            items.extend(await fetch_feed(url))
        if items:
            risultati[cat] = items[:5]
    return risultati

def formatta(offerte):
    ora = datetime.now().strftime("%d/%m/%Y %H:%M")
    testo = f"🤖 *OFFERTE GUADAGNO ONLINE*\n📅 {ora}\n{'─'*30}\n\n"
    for cat, items in offerte.items():
        testo += f"{cat}\n"
        for i, item in enumerate(items, 1):
            testo += f"{i}. [{item['titolo']}]({item['link']})\n"
        testo += "\n"
    return testo or "⚠️ Nessuna offerta trovata."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"👋 *Ciao! Bot Offerte attivo!*\n\n"
        f"🆔 Chat ID: `{update.effective_chat.id}`\n\n"
        f"/offerte — Tutte le offerte ora\n"
        f"/info — Info bot\n\n"
        f"⏰ Invio automatico ogni 24 ore!",
        parse_mode="Markdown"
    )

async def cmd_offerte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Cerco offerte...")
    offerte = await raccogli()
    await update.message.reply_text(formatta(offerte), parse_mode="Markdown", disable_web_page_preview=True)

async def cmd_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot Offerte Guadagno Online\n⏰ Aggiornamento ogni 24 ore automatico!", parse_mode="Markdown")

async def invia_automatico(context: ContextTypes.DEFAULT_TYPE):
    offerte = await raccogli()
    await context.bot.send_message(chat_id=CHAT_ID, text=formatta(offerte), parse_mode="Markdown", disable_web_page_preview=True)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("offerte", cmd_offerte))
    app.add_handler(CommandHandler("info", cmd_info))
    app.job_queue.run_repeating(invia_automatico, interval=86400, first=30)
    print("🚀 Bot avviato!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
  