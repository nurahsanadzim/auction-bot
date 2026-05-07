from telegram import Update
from telegram.ext import ContextTypes

from config import GROUP_ID
from core.csv_store import get_user, get_item, load_bids, append_bid, new_bid
from core.auction_logic import get_top_bid


def _fmt(amount: int) -> str:
    return "Rp" + f"{amount:,}".replace(",", ".")


async def bid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    user_id = update.effective_user.id
    user = get_user(user_id)
    if not user or not user.active:
        await update.message.reply_text("You're not a participant. Use /participate first.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("Usage: /bid <item_id> <amount>")
        return

    item_id = context.args[0].lower()
    try:
        amount = int(context.args[1].replace(".", "").replace(",", ""))
    except ValueError:
        await update.message.reply_text("Amount must be a number.")
        return

    item = get_item(item_id)
    if not item or not item.active:
        await update.message.reply_text("Item ID not found.")
        return

    if amount < item.starting_price:
        await update.message.reply_text(
            f"Bid must be at least the starting price: {_fmt(item.starting_price)}"
        )
        return

    bids = load_bids()
    top = get_top_bid(item_id, bids)
    if top and amount <= top.amount:
        await update.message.reply_text(
            f"Bid must be higher than current top: {_fmt(top.amount)}"
        )
        return

    append_bid(new_bid(item_id, user_id, amount))
    await update.message.reply_text(
        f"Bid placed: {_fmt(amount)} on [{item_id}] {item.name}"
    )
