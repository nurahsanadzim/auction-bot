from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    telegram_id: int
    username: str
    joined_at: datetime
    active: bool


@dataclass
class Item:
    id: str
    name: str
    starting_price: int
    detail: str
    link: str
    active: bool


@dataclass
class Bid:
    bid_id: str
    item_id: str
    telegram_id: int
    amount: int
    timestamp: datetime
    revoked: bool
