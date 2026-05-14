import logging

from telegram import BotCommand, BotCommandScopeAllGroupChats
from telegram.ext import Application, CommandHandler

from config import BOT_TOKEN
from core.csv_store import init_data_dir
from commands.participate import participate
from commands.withdraw import withdraw
from commands.list_items import list_items
from commands.my_auctions import my_auctions
from commands.bid import bid
from commands.revoke import revoke
from commands.winners import winners
from commands.help import help_command
from commands.rules import rules

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


GROUP_COMMANDS = [
    BotCommand("participate", "Join the auction"),
    BotCommand("withdraw",    "Leave and revoke all your bids"),
    BotCommand("list_items",  "View all items and current leading bids"),
    BotCommand("my_auctions", "View your bids and status"),
    BotCommand("bid",         "Place a bid — /bid <item_id> <amount>"),
    BotCommand("revoke",      "Revoke your bid — /revoke <item_id>"),
    BotCommand("winners",     "Show final winners (after auction ends)"),
    BotCommand("rules",       "Show auction rules"),
    BotCommand("help",        "List all commands"),
]


async def post_init(app: Application) -> None:
    await app.bot.set_my_commands(GROUP_COMMANDS, scope=BotCommandScopeAllGroupChats())


def main():
    init_data_dir()

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("participate", participate))
    app.add_handler(CommandHandler("withdraw", withdraw))
    app.add_handler(CommandHandler("list_items", list_items))
    app.add_handler(CommandHandler("my_auctions", my_auctions))
    app.add_handler(CommandHandler("bid", bid))
    app.add_handler(CommandHandler("revoke", revoke))
    app.add_handler(CommandHandler("winners", winners))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("rules", rules))

    app.run_polling()


if __name__ == "__main__":
    main()
