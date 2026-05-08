from telegram import Update
from telegram.ext import ContextTypes

from config import GROUP_ID, auction_has_ended
from core.csv_store import get_user, load_items, load_bids
from core.auction_logic import get_leading_bid, resolve_at_close


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

    ended = auction_has_ended()

    if ended:
        results = resolve_at_close(items, bids)
        lines = ["Auction Results:\n"]
    else:
        lines = ["Your Auctions:\n"]

    for item in items:
        my_bid = max(
            (b for b in my_active_bids if b.item_id == item.id),
            key=lambda b: b.amount,
            default=None,
        )
        if not my_bid:
            continue

        lines.append(f"[{item.id}] {item.name}")

        if ended:
            winner_bid = results.get(item.id)
            won = winner_bid is not None and winner_bid.telegram_id == user_id
            status = "WON" if won else "not won"
            lines.append(f"  Your bid: {_fmt(my_bid.amount)} — {status}")
        else:
            leading = get_leading_bid(item.id, bids)
            is_leading = leading is not None and leading.telegram_id == user_id
            if is_leading:
                lines.append(f"  Your bid: {_fmt(my_bid.amount)} — leading")
            else:
                lead_str = _fmt(leading.amount) if leading else "none"
                lines.append(f"  Your bid: {_fmt(my_bid.amount)} — not leading (leading: {lead_str})")

        lines.append("")

    await update.message.reply_text("\n".join(lines).strip())
