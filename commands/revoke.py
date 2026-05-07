from telegram import Update
from telegram.ext import ContextTypes

from config import GROUP_ID
from core.csv_store import get_user, get_item, load_bids, save_bids


async def revoke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    user_id = update.effective_user.id
    user = get_user(user_id)
    if not user or not user.active:
        await update.message.reply_text("You're not a participant. Use /participate first.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /revoke <item_id>")
        return

    item_id = context.args[0].lower()
    item = get_item(item_id)
    if not item or not item.active:
        await update.message.reply_text("Item ID not found.")
        return

    bids = load_bids()
    active_bid = next(
        (b for b in bids if b.item_id == item_id and b.telegram_id == user_id and not b.revoked),
        None,
    )
    if not active_bid:
        await update.message.reply_text("You have no active bid on this item.")
        return

    active_bid.revoked = True
    save_bids(bids)
    await update.message.reply_text(
        f"Your bid on [{item_id}] {item.name} has been revoked."
    )
