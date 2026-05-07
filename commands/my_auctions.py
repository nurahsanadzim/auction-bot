from telegram import Update
from telegram.ext import ContextTypes

from config import GROUP_ID
from core.csv_store import get_user, load_items, load_bids
from core.auction_logic import get_top_bid, resolve_big_auction


def _fmt(amount: int) -> str:
    return "Rp" + f"{amount:,}".replace(",", ".")


async def my_auctions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type != "private" and chat.id != GROUP_ID:
        return

    user_id = update.effective_user.id
    user = get_user(user_id)
    if not user or not user.active:
        await update.message.reply_text("You're not a participant. Use /participate first.")
        return

    items = load_items()
    bids = load_bids()

    my_active_bids = [b for b in bids if b.telegram_id == user_id and not b.revoked]
    if not my_active_bids:
        await update.message.reply_text("You have no active bids.")
        return

    big_items = [i for i in items if i.type == "big" and i.active]
    big_results = resolve_big_auction(big_items, bids)

    lines = ["Your Auctions:\n"]
    for item in items:
        my_bid = next((b for b in my_active_bids if b.item_id == item.id), None)
        if not my_bid:
            continue

        if item.type == "big":
            winner_bid = big_results.get(item.id)
            winning = winner_bid is not None and winner_bid.telegram_id == user_id
        else:
            top = get_top_bid(item.id, bids)
            winning = top is not None and top.telegram_id == user_id

        status = "WINNING" if winning else "outbid"
        lines.append(f"[{item.id}] {item.name}")
        lines.append(f"  Your bid: {_fmt(my_bid.amount)} — {status}\n")

    await update.message.reply_text("\n".join(lines).strip())
