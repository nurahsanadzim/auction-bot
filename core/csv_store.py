import csv
import uuid
from datetime import datetime, timezone
from filelock import FileLock

from config import DATA_DIR, USERS_CSV, ITEMS_CSV, BIDS_CSV
from core.models import User, Item, Bid

USERS_HEADERS = ["telegram_id", "username", "joined_at", "active"]
ITEMS_HEADERS = ["id", "name", "type", "starting_price", "detail", "link", "active", "timer"]
BIDS_HEADERS  = ["bid_id", "item_id", "telegram_id", "amount", "timestamp", "revoked"]


def init_data_dir():
    DATA_DIR.mkdir(exist_ok=True)
    for path, headers in [
        (USERS_CSV, USERS_HEADERS),
        (ITEMS_CSV, ITEMS_HEADERS),
        (BIDS_CSV,  BIDS_HEADERS),
    ]:
        if not path.exists():
            with open(path, "w", newline="") as f:
                csv.DictWriter(f, fieldnames=headers).writeheader()


# ── Users ──────────────────────────────────────────────────────────────────

def _parse_user(row: dict) -> User:
    return User(
        telegram_id=int(row["telegram_id"]),
        username=row["username"],
        joined_at=datetime.fromisoformat(row["joined_at"]),
        active=row["active"] == "True",
    )


def load_users() -> list[User]:
    with open(USERS_CSV, newline="") as f:
        return [_parse_user(r) for r in csv.DictReader(f)]


def save_users(users: list[User]):
    lock = FileLock(str(USERS_CSV) + ".lock")
    with lock:
        with open(USERS_CSV, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=USERS_HEADERS)
            w.writeheader()
            for u in users:
                w.writerow({
                    "telegram_id": u.telegram_id,
                    "username":    u.username,
                    "joined_at":   u.joined_at.isoformat(),
                    "active":      u.active,
                })


def get_user(telegram_id: int) -> User | None:
    return next((u for u in load_users() if u.telegram_id == telegram_id), None)


def upsert_user(user: User):
    users = load_users()
    for i, u in enumerate(users):
        if u.telegram_id == user.telegram_id:
            users[i] = user
            save_users(users)
            return
    users.append(user)
    save_users(users)


# ── Items ──────────────────────────────────────────────────────────────────

def _parse_item(row: dict) -> Item:
    raw_timer = row.get("timer", "")
    return Item(
        id=row["id"],
        name=row["name"],
        type=row["type"],
        starting_price=int(row["starting_price"]),
        detail=row["detail"],
        link=row["link"],
        active=row["active"] == "True",
        timer=datetime.fromisoformat(raw_timer) if raw_timer else None,
    )


def load_items() -> list[Item]:
    with open(ITEMS_CSV, newline="") as f:
        return [_parse_item(r) for r in csv.DictReader(f)]


def save_items(items: list[Item]):
    lock = FileLock(str(ITEMS_CSV) + ".lock")
    with lock:
        with open(ITEMS_CSV, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=ITEMS_HEADERS)
            w.writeheader()
            for i in items:
                w.writerow({
                    "id":            i.id,
                    "name":          i.name,
                    "type":          i.type,
                    "starting_price": i.starting_price,
                    "detail":        i.detail,
                    "link":          i.link,
                    "active":        i.active,
                    "timer":         i.timer.isoformat() if i.timer else "",
                })


def get_item(item_id: str) -> Item | None:
    return next((i for i in load_items() if i.id == item_id), None)


# ── Bids ───────────────────────────────────────────────────────────────────

def _parse_bid(row: dict) -> Bid:
    return Bid(
        bid_id=row["bid_id"],
        item_id=row["item_id"],
        telegram_id=int(row["telegram_id"]),
        amount=int(row["amount"]),
        timestamp=datetime.fromisoformat(row["timestamp"]),
        revoked=row["revoked"] == "True",
    )


def load_bids() -> list[Bid]:
    with open(BIDS_CSV, newline="") as f:
        return [_parse_bid(r) for r in csv.DictReader(f)]


def append_bid(bid: Bid):
    lock = FileLock(str(BIDS_CSV) + ".lock")
    with lock:
        with open(BIDS_CSV, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=BIDS_HEADERS)
            w.writerow({
                "bid_id":      bid.bid_id,
                "item_id":     bid.item_id,
                "telegram_id": bid.telegram_id,
                "amount":      bid.amount,
                "timestamp":   bid.timestamp.isoformat(),
                "revoked":     bid.revoked,
            })


def save_bids(bids: list[Bid]):
    lock = FileLock(str(BIDS_CSV) + ".lock")
    with lock:
        with open(BIDS_CSV, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=BIDS_HEADERS)
            w.writeheader()
            for b in bids:
                w.writerow({
                    "bid_id":      b.bid_id,
                    "item_id":     b.item_id,
                    "telegram_id": b.telegram_id,
                    "amount":      b.amount,
                    "timestamp":   b.timestamp.isoformat(),
                    "revoked":     b.revoked,
                })


def new_bid(item_id: str, telegram_id: int, amount: int) -> Bid:
    return Bid(
        bid_id=str(uuid.uuid4()),
        item_id=item_id,
        telegram_id=telegram_id,
        amount=amount,
        timestamp=datetime.now(timezone.utc),
        revoked=False,
    )
