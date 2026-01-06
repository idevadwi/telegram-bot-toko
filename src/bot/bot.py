import pandas as pd
import os
from glob import glob
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters
)

from core.config import load_config
from core.logger import setup_logging, get_logger
from core.exceptions import TelegramBotError

# Load configuration
config = load_config()
setup_logging(config)
logger = get_logger('bot')

# Global Data
df = pd.DataFrame()
csv_path = ""
csv_loaded_at = None


# === Load Latest CSV ===
def get_latest_csv(folder_path):
    """Get the latest CSV file from folder"""
    list_of_files = glob(os.path.join(folder_path, "*.csv"))
    if not list_of_files:
        raise TelegramBotError("❌ Tidak ada file CSV ditemukan.")
    latest_file = max(list_of_files, key=os.path.getmtime)
    return latest_file


def load_csv():
    """Load the latest CSV file"""
    global df, csv_path, csv_loaded_at
    csv_path = get_latest_csv(str(config.paths.exports_dir))
    df = pd.read_csv(csv_path)
    csv_loaded_at = datetime.fromtimestamp(os.path.getmtime(csv_path))
    logger.info(f"Reloaded CSV: {csv_path}")


# === Search Function ===
def search_products(keyword):
    """Search products by keyword"""
    keyword = keyword.strip().upper()
    results = df[df["namaitem"].str.contains(keyword, case=False, na=False)].sort_values(by="namaitem")

    if results.empty:
        return "❌ Barang tidak ditemukan. Coba dengan kata lain."

    response = "📦 *Hasil Pencarian:*\n"
    count = 0
    for _, row in results.iterrows():
        response += (
            f"🔹 *{row['namaitem']}*\n"
            f"   📦 Konversi: {row['konversi']}\n"
            f"   📏 Satuan: {row['satuan']}\n"
            f"   💰 Harga Pokok: Rp{row['hargapokok']:,.0f}\n"
            f"   🛒 Harga Jual: Rp{row['hargajual']:,.0f}\n\n"
        )
        count += 1
        if count >= config.search_results_limit:
            response += "⚠️ *Terlalu banyak hasil. Gunakan kata yang lebih spesifik.*"
            break

    return response


# === Telegram Handlers ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    try:
        query = update.message.text.strip()
        response = search_products(query)
        await update.message.reply_text(response, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text("❌ Terjadi kesalahan. Silakan coba lagi.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_text = (
        "👋 *Selamat datang!*\n"
        "Ketik *nama barang* untuk mencari harga.\n\n"
        "Perintah tambahan:\n"
        "/reload - Muat ulang file CSV\n"
        "/version - Versi data saat ini\n\n"
        "Contoh:\n"
        "🔍 *BERAS* → Menampilkan semua jenis beras.\n"
        "🔍 *SABUN* → Menampilkan semua produk sabun.\n"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")


async def reload_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /reload command"""
    try:
        load_csv()
        await update.message.reply_text(
            f"✅ File CSV dimuat ulang dari:\n`{csv_path}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error reloading CSV: {e}")
        await update.message.reply_text(f"❌ Gagal memuat ulang CSV: {e}")


async def show_version(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /version command"""
    if csv_loaded_at:
        await update.message.reply_text(
            f"📦 Versi data saat ini:\n`{csv_loaded_at.strftime('%Y-%m-%d %H:%M:%S')}`",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ CSV belum dimuat.")


def main():
    """Main function to run the bot"""
    # Load CSV at startup
    try:
        load_csv()
    except Exception as e:
        logger.error(f"Failed to load CSV at startup: {e}")

    # Initialize Bot
    app = ApplicationBuilder().token(config.telegram.bot_token).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reload", reload_csv))
    app.add_handler(CommandHandler("version", show_version))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the Bot
    logger.info("Bot is running...")
    app.run_polling()


if __name__ == '__main__':
    main()
