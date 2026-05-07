import logging

from telegram.ext import Application, CommandHandler

from config import BOT_TOKEN
from core.csv_store import init_data_dir
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

    app.run_polling()


if __name__ == "__main__":
    main()
