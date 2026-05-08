import os
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
GROUP_ID  = int(os.environ["GROUP_ID"])
DATA_DIR  = Path("data/")
USERS_CSV = DATA_DIR / "users.csv"
ITEMS_CSV = DATA_DIR / "items.csv"
BIDS_CSV  = DATA_DIR / "bids.csv"

_start = os.environ.get("AUCTION_START", "")
_end   = os.environ.get("AUCTION_END", "")
AUCTION_START = datetime.fromisoformat(_start) if _start else None
AUCTION_END   = datetime.fromisoformat(_end)   if _end   else None


def auction_is_open() -> bool:
    now = datetime.now(timezone.utc)
    if AUCTION_START and now < AUCTION_START:
        return False
    if AUCTION_END and now > AUCTION_END:
        return False
    return True


def auction_has_ended() -> bool:
    if not AUCTION_END:
        return False
    return datetime.now(timezone.utc) > AUCTION_END
