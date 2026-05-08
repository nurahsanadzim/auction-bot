from telegram import Update
from telegram.ext import ContextTypes

from config import GROUP_ID, auction_has_ended
from core.csv_store import load_items, load_bids, get_user
from core.auction_logic import resolve_at_close


def _fmt(amount: int) -> str:
    return "Rp" + f"{amount:,}".replace(",", ".")


async def winners(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    if not auction_has_ended():
        await update.message.reply_text("Auction is still ongoing. Winners will be announced after it ends.")
        return

    items = load_items()
    bids = load_bids()
    results = resolve_at_close(items, bids)

    lines = ["Auction Winners:\n"]

    for item in [i for i in items if i.active]:
        winner_bid = results.get(item.id)
        if winner_bid:
            winner_user = get_user(winner_bid.telegram_id)
            winner_name = f"@{winner_user.username}" if winner_user else f"user {winner_bid.telegram_id}"
            lines.append(f"[{item.id}] {item.name} → {winner_name} — {_fmt(winner_bid.amount)}")
        else:
            lines.append(f"[{item.id}] {item.name} → No winner")

    await update.message.reply_text("\n".join(lines))
