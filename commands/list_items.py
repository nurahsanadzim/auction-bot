from datetime import timezone, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from config import GROUP_ID, auction_is_open, auction_has_ended, AUCTION_END
from core.csv_store import load_items, load_bids, get_user
from core.auction_logic import get_leading_bid

WIB = timezone(timedelta(hours=7))


def _fmt(amount: int) -> str:
    return "Rp" + f"{amount:,}".replace(",", ".")


async def list_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    items = [i for i in load_items() if i.active]
    if not items:
        await update.message.reply_text("No auction items available.")
        return

    bids = load_bids()

    if auction_has_ended():
        status_line = "Auction has ended. Use /winners to see results."
    elif auction_is_open():
        end_str = AUCTION_END.astimezone(WIB).strftime("%Y-%m-%d %H:%M WIB") if AUCTION_END else "TBD"
        status_line = f"Auction is OPEN — closes at {end_str}"
    else:
        status_line = "Auction has not started yet."

    lines = [status_line, ""]

    for item in items:
        lines.append(f"[{item.id}] {item.name}")
        lines.append(f"  Starting price: {_fmt(item.starting_price)}")

        if item.detail:
            lines.append(f"  {item.detail}")
        if item.link:
            lines.append(f"  {item.link}")

        leading = get_leading_bid(item.id, bids)
        if leading:
            leading_user = get_user(leading.telegram_id)
            leading_name = f"@{leading_user.username}" if leading_user else "Unknown"
            lines.append(f"  Leading: {_fmt(leading.amount)} by {leading_name}")
        else:
            lines.append("  Leading: No bids yet")

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
