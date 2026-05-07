from telegram import Update
from telegram.ext import ContextTypes

from config import GROUP_ID
from core.csv_store import load_items, load_bids
from core.auction_logic import get_top_bid


def _fmt(amount: int) -> str:
    return "Rp" + f"{amount:,}".replace(",", ".")


async def list_big(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    items = [i for i in load_items() if i.type == "big" and i.active]
    if not items:
        await update.message.reply_text("No active big auction items.")
        return

    bids = load_bids()
    lines = []

    for item in items:
        top = get_top_bid(item.id, bids)
        top_str = f"{_fmt(top.amount)} (Anonymous)" if top else "No bids yet"
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
