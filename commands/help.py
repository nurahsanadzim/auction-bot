from telegram import Update
from telegram.ext import ContextTypes

HELP_TEXT = """
*Auction Bot Commands*

/participate — Join the auction
/withdraw — Leave and revoke all your bids
/list\_big — View all big auction items
/list\_normal — View all normal auction items
/my\_auctions — View your bids and win status
/bid <item\_id> <amount> — Place a bid on an item
/revoke <item\_id> — Revoke your bid on an item
/help — Show this message
""".strip()


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")
