import logging
from datetime import datetime, timezone

from telegram.ext import Application, CommandHandler, ContextTypes

from config import BOT_TOKEN
from core.csv_store import init_data_dir, load_items, save_items
from commands.participate import participate
from commands.withdraw import withdraw
from commands.list_big import list_big
from commands.list_normal import list_normal
from commands.my_auctions import my_auctions
from commands.bid import bid
from commands.revoke import revoke
from commands.help import help_command

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


async def check_timers(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(timezone.utc)
    items = load_items()
    changed = False
    for item in items:
        if item.active and item.timer and now >= item.timer:
            item.active = False
            changed = True
            logging.info("Auto-closed item %s (timer expired)", item.id)
    if changed:
        save_items(items)


def main():
    init_data_dir()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("participate", participate))
    app.add_handler(CommandHandler("withdraw", withdraw))
    app.add_handler(CommandHandler("list_big", list_big))
    app.add_handler(CommandHandler("list_normal", list_normal))
    app.add_handler(CommandHandler("my_auctions", my_auctions))
    app.add_handler(CommandHandler("bid", bid))
    app.add_handler(CommandHandler("revoke", revoke))
    app.add_handler(CommandHandler("help", help_command))

    app.job_queue.run_repeating(check_timers, interval=60, first=10)

    app.run_polling()


if __name__ == "__main__":
    main()
