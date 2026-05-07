from datetime import datetime, timezone

from telegram import Update
from telegram.ext import ContextTypes

from config import GROUP_ID
from core.csv_store import get_user, upsert_user
from core.models import User


async def participate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    tg_user = update.effective_user
    existing = get_user(tg_user.id)

    if existing:
        if existing.active:
            await update.message.reply_text("You're already a participant.")
        else:
            existing.active = True
            upsert_user(existing)
            await update.message.reply_text("Welcome back! You've rejoined the auction.")
        return

    user = User(
        telegram_id=tg_user.id,
        username=tg_user.username or str(tg_user.id),
        joined_at=datetime.now(timezone.utc),
        active=True,
    )
    upsert_user(user)
    await update.message.reply_text("You're now registered as a participant!")
