from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
)

from config import GROUP_ID, auction_is_open
from core.csv_store import get_user, get_item, load_bids, append_bid, new_bid
from core.auction_logic import get_leading_bid

BID_ITEM, BID_AMOUNT = range(2)


def _fmt(amount: int) -> str:
    return "Rp" + f"{amount:,}".replace(",", ".")


async def _guard(update: Update) -> bool:
    """Return False and reply if pre-conditions fail."""
    if update.effective_chat.id != GROUP_ID:
        return False
    if not auction_is_open():
        await update.message.reply_text("Auction is not currently open for bidding.")
        return False
    user = get_user(update.effective_user.id)
    if not user or not user.active:
        await update.message.reply_text("You're not a participant. Use /participate first.")
        return False
    return True


async def _execute(update: Update, user_id: int, item_id: str, amount_str: str) -> int:
    try:
        amount = int(amount_str.replace(".", "").replace(",", ""))
    except ValueError:
        await update.message.reply_text("Amount must be a number.")
        return ConversationHandler.END

    if amount % 20000 != 0:
        await update.message.reply_text(
            "Bid amount must be a multiple of Rp20.000 (e.g. 20.000, 40.000, 200.000)."
        )
        return ConversationHandler.END

    item = get_item(item_id)
    if not item:
        await update.message.reply_text("Item ID not found.")
        return ConversationHandler.END
    if not item.active:
        await update.message.reply_text(f"[{item_id}] {item.name} is not available for bidding.")
        return ConversationHandler.END

    if amount < item.starting_price:
        await update.message.reply_text(
            f"Bid must be at least the starting price: {_fmt(item.starting_price)}"
        )
        return ConversationHandler.END

    bids = load_bids()
    leading = get_leading_bid(item_id, bids)
    if leading and amount <= leading.amount:
        leading_user = get_user(leading.telegram_id)
        leading_name = f"@{leading_user.username}" if leading_user else "someone"
        await update.message.reply_text(
            f"Bid must be higher than current leading: {_fmt(leading.amount)} by {leading_name}"
        )
        return ConversationHandler.END

    append_bid(new_bid(item_id, user_id, amount))
    await update.message.reply_text(f"Bid placed: {_fmt(amount)} on [{item_id}] {item.name}")
    return ConversationHandler.END


async def bid_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await _guard(update):
        return ConversationHandler.END

    if len(context.args) == 2:
        return await _execute(update, update.effective_user.id, context.args[0].lower(), context.args[1])

    await update.message.reply_text("Which item do you want to bid on? Send the item ID (e.g. 1, 2, 3)\n\nSend /cancel to abort.")
    return BID_ITEM


async def bid_receive_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["bid_item"] = update.message.text.strip().lower()
    await update.message.reply_text("How much do you want to bid? (must be a multiple of Rp20.000)")
    return BID_AMOUNT


async def bid_receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    item_id = context.user_data.pop("bid_item", None)
    return await _execute(update, update.effective_user.id, item_id, update.message.text.strip())


async def bid_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("bid_item", None)
    await update.message.reply_text("Bid cancelled.")
    return ConversationHandler.END


bid_handler = ConversationHandler(
    entry_points=[CommandHandler("bid", bid_start)],
    states={
        BID_ITEM:   [MessageHandler(filters.TEXT & ~filters.COMMAND, bid_receive_item)],
        BID_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bid_receive_amount)],
    },
    fallbacks=[CommandHandler("cancel", bid_cancel)],
    per_chat=True,
    per_user=True,
)
