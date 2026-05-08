from telegram import Update
from telegram.ext import ContextTypes

from config import GROUP_ID, auction_is_open
from core.csv_store import get_user, get_item, load_bids, append_bid, new_bid
from core.auction_logic import get_leading_bid


def _fmt(amount: int) -> str:
    return "Rp" + f"{amount:,}".replace(",", ".")


async def bid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    if not auction_is_open():
        await update.message.reply_text("Auction is not currently open for bidding.")
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
    if not item:
        await update.message.reply_text("Item ID not found.")
        return
    if not item.active:
        await update.message.reply_text(f"[{item_id}] {item.name} is not available for bidding.")
        return

    if amount < item.starting_price:
        await update.message.reply_text(
            f"Bid must be at least the starting price: {_fmt(item.starting_price)}"
        )
        return

    bids = load_bids()
    leading = get_leading_bid(item_id, bids)
    if leading and amount <= leading.amount:
        leading_user = get_user(leading.telegram_id)
        leading_name = f"@{leading_user.username}" if leading_user else "someone"
        await update.message.reply_text(
            f"Bid must be higher than current leading: {_fmt(leading.amount)} by {leading_name}"
        )
        return

    append_bid(new_bid(item_id, user_id, amount))
    await update.message.reply_text(
        f"Bid placed: {_fmt(amount)} on [{item_id}] {item.name}"
    )
