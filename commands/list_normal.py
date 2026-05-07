from telegram import Update
from telegram.ext import ContextTypes

from config import GROUP_ID
from core.csv_store import load_items, load_bids, get_user
from core.auction_logic import get_top_bid


def _fmt(amount: int) -> str:
    return "Rp" + f"{amount:,}".replace(",", ".")


async def list_normal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    items = [i for i in load_items() if i.type == "normal" and i.active]
    if not items:
        await update.message.reply_text("No active normal auction items.")
        return

    bids = load_bids()
    lines = []

    for item in items:
        top = get_top_bid(item.id, bids)
        if top:
            top_user = get_user(top.telegram_id)
            top_name = f"@{top_user.username}" if top_user else "Unknown"
            top_str = f"{_fmt(top.amount)} by {top_name}"
        else:
            top_str = "No bids yet"
        lines.append(f"[{item.id}] {item.name} — Current top: {top_str}")
        lines.append(f"  Starting price: {_fmt(item.starting_price)}")
        if item.detail:
            lines.append(f"  {item.detail}")
        if item.link:
            lines.append(f"  {item.link}")

        item_bids = sorted(
            [b for b in bids if b.item_id == item.id and not b.revoked],
            key=lambda b: b.amount,
            reverse=True,
        )
        if item_bids:
            history = ", ".join(_fmt(b.amount) for b in item_bids)
            lines.append(f"  Bid history: {history} (all Anonymous)")

        lines.append("")

    await update.message.reply_text("\n".join(lines).strip())
