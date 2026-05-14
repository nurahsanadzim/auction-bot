from telegram import Update
from telegram.ext import ContextTypes

HELP_TEXT = r"""
*Auction Bot Commands*

/participate — Join the auction
/withdraw — Leave and revoke all your bids
/list\_items — View all auction items and leading bids
/my\_auctions — View your bids and status
/bid <item\_id> <amount> — Place a bid on an item
/revoke <item\_id> — Revoke your bid on an item
/winners — Show winners after auction ends
/rules — Show auction rules
/cancel — Cancel the current action
/help — Show this message
""".strip()


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")
