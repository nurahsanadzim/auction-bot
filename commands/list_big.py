from telegram import Update
from telegram.ext import ContextTypes

from config import GROUP_ID
from core.csv_store import load_items, load_bids, get_user
from core.auction_logic import get_top_bid


def _fmt(amount: int) -> str:
    return "Rp" + f"{amount:,}".replace(",", ".")


async def list_big(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    items = [i for i in load_items() if i.type == "big"]
    if not items:
        await update.message.reply_text("No big auction items.")
        return

    bids = load_bids()
    lines = []

    for item in items:
        status = "CLOSED" if not item.active else "OPEN"
        lines.append(f"[{item.id}] {item.name} [{status}]")
        lines.append(f"  Starting price: {_fmt(item.starting_price)}")

        if item.timer:
            timer_str = item.timer.astimezone().strftime("%Y-%m-%d %H:%M %Z")
            label = "Closed at" if not item.active else "Closes at"
            lines.append(f"  {label}: {timer_str}")

        if item.detail:
            lines.append(f"  {item.detail}")
        if item.link:
            lines.append(f"  {item.link}")

        top = get_top_bid(item.id, bids)
        if top:
            top_user = get_user(top.telegram_id)
            top_name = f"@{top_user.username}" if top_user else "Unknown"
            lines.append(f"  Current top: {_fmt(top.amount)} by {top_name}")
        else:
            lines.append("  Current top: No bids yet")

        item_bids = sorted(
            [b for b in bids if b.item_id == item.id and not b.revoked],
            key=lambda b: b.amount,
            reverse=True,
        )
        if item_bids:
            history = ", ".join(_fmt(b.amount) for b in item_bids)
            lines.append(f"  Bid history: {history}")

        lines.append("")

    await update.message.reply_text("\n".join(lines).strip())
