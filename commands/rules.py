from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("Read Auction Rules", url="https://github.com/nurahsanadzim/auction-bot/blob/main/README.id.md#cara-kerjanya")
    ]])
    await update.message.reply_text("Auction rules and how to participate:", reply_markup=keyboard)
