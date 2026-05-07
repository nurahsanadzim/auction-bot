import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
GROUP_ID  = int(os.environ["GROUP_ID"])
DATA_DIR  = Path("data/")
USERS_CSV = DATA_DIR / "users.csv"
ITEMS_CSV = DATA_DIR / "items.csv"
BIDS_CSV  = DATA_DIR / "bids.csv"
