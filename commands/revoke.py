from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
)

from config import GROUP_ID, auction_is_open
from core.csv_store import get_user, get_item, load_bids, save_bids

REVOKE_ITEM = 0


async def _execute(update: Update, user_id: int, item_id: str) -> int:
    item = get_item(item_id)
    if not item or not item.active:
        await update.message.reply_text("Item ID not found.")
        return ConversationHandler.END

    bids = load_bids()
    active_bid = next(
        (b for b in bids if b.item_id == item_id and b.telegram_id == user_id and not b.revoked),
        None,
    )
    if not active_bid:
        await update.message.reply_text("You have no active bid on this item.")
        return ConversationHandler.END

    active_bid.revoked = True
    save_bids(bids)
    await update.message.reply_text(f"Your bid on [{item_id}] {item.name} has been revoked.")
    return ConversationHandler.END


async def revoke_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_chat.id != GROUP_ID:
        return ConversationHandler.END

    if not auction_is_open():
        await update.message.reply_text("Auction is not currently open. Bids cannot be revoked.")
        return ConversationHandler.END

    user_id = update.effective_user.id
    user = get_user(user_id)
    if not user or not user.active:
        await update.message.reply_text("You're not a participant. Use /participate first.")
        return ConversationHandler.END

    if context.args:
        return await _execute(update, user_id, context.args[0].lower())

    await update.message.reply_text("Which item do you want to revoke your bid on? Send the item ID (e.g. 1, 2, 3)\n\nSend /cancel to abort.")
    return REVOKE_ITEM


async def revoke_receive_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await _execute(update, update.effective_user.id, update.message.text.strip().lower())


async def revoke_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Revoke cancelled.")
    return ConversationHandler.END


revoke_handler = ConversationHandler(
    entry_points=[CommandHandler("revoke", revoke_start)],
    states={
        REVOKE_ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, revoke_receive_item)],
    },
    fallbacks=[CommandHandler("cancel", revoke_cancel)],
    per_chat=True,
    per_user=True,
)
