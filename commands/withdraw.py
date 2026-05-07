from telegram import Update
from telegram.ext import ContextTypes

from config import GROUP_ID
from core.csv_store import get_user, upsert_user, load_bids, save_bids


async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    user_id = update.effective_user.id
    user = get_user(user_id)
    if not user or not user.active:
        await update.message.reply_text("You're not a participant. Use /participate first.")
        return

    user.active = False
    upsert_user(user)

    bids = load_bids()
    changed = False
    for bid in bids:
        if bid.telegram_id == user_id and not bid.revoked:
            bid.revoked = True
            changed = True
    if changed:
        save_bids(bids)

    await update.message.reply_text(
        "You've withdrawn from the auction. All your bids have been revoked."
    )
