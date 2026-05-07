from telegram import Update
from telegram.ext import ContextTypes

from config import GROUP_ID
from core.csv_store import get_user, get_item, load_items, load_bids, save_bids, append_bid, new_bid
from core.auction_logic import get_top_bid, resolve_big_auction


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
        top_user = get_user(top.telegram_id)
        top_name = f"@{top_user.username}" if top_user else "someone"
        await update.message.reply_text(
            f"Bid must be higher than current top: {_fmt(top.amount)} by {top_name}"
        )
        return

    # Big auction: enforce one active big bid per user
    if item.type == "big":
        all_items = load_items()
        big_items = [i for i in all_items if i.type == "big" and i.active]
        big_results = resolve_big_auction(big_items, bids)

        other_big_bids = [
            b for b in bids
            if b.telegram_id == user_id
            and not b.revoked
            and b.item_id != item_id
            and any(i.id == b.item_id and i.type == "big" for i in big_items)
        ]

        for other_bid in other_big_bids:
            winner = big_results.get(other_bid.item_id)
            if winner and winner.telegram_id == user_id:
                await update.message.reply_text(
                    f"You're currently winning [{other_bid.item_id}]. "
                    f"Revoke it first with /revoke {other_bid.item_id} before bidding on another big item."
                )
                return

        # Not winning those — auto-revoke them
        changed = False
        for b in bids:
            if b in other_big_bids:
                b.revoked = True
                changed = True
        if changed:
            save_bids(bids)

    append_bid(new_bid(item_id, user_id, amount))
    await update.message.reply_text(
        f"Bid placed: {_fmt(amount)} on [{item_id}] {item.name}"
    )
