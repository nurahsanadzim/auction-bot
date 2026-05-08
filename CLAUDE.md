# CLAUDE.md — Telegram Auction Bot

## Project Overview

A Python-based Telegram bot for managing auctions within a group chat. Users opt-in to participate and interact exclusively via bot commands. All data persists in local CSV files.

---

## Environment

- **Local dev**: WSL (Ubuntu) — project lives at `~/auction-bot/`
- **Version control**: GitHub — push/pull via `git` in WSL
- **Data directory**: `auction-bot/data/` is **gitignored** — never committed (contains user PII and bid data)

### Git Setup

`.gitignore` must include:

```
data/
.env
__pycache__/
*.pyc
venv/
```

Seed/sample data for local testing should live in `data/` only — never commit real or test CSVs.

---

## Architecture

### Stack

- **Language**: Python 3.10+
- **Framework**: `python-telegram-bot` (v20+, async)
- **Storage**: Local CSV files (no external DB)
- **Deployment**: Single process, runs in foreground or as systemd service

### File Structure

```
auction-bot/
├── bot.py                  # Entry point, registers handlers
├── commands/
│   ├── participate.py
│   ├── withdraw.py
│   ├── list_items.py
│   ├── my_auctions.py
│   ├── bid.py
│   ├── revoke.py
│   ├── winners.py
│   └── help.py
├── data/                   # ⚠ gitignored — local only
│   ├── users.csv           # Registered participants
│   ├── items.csv           # Auction items
│   └── bids.csv            # All bid records
├── core/
│   ├── csv_store.py        # CRUD abstraction for CSV
│   ├── auction_logic.py    # Auction resolution logic
│   └── models.py           # Dataclasses: User, Item, Bid
├── config.py               # BOT_TOKEN, GROUP_ID, auction window, paths
├── .env                    # ⚠ gitignored — secrets only
├── .env.example            # committed — template with empty values
├── .gitignore
├── requirements.txt
└── CLAUDE.md
```

---

## Data Models

### `users.csv`

| Column      | Type     | Notes                     |
|-------------|----------|---------------------------|
| telegram_id | int      | Primary key               |
| username    | str      | @handle                   |
| joined_at   | datetime | ISO 8601                  |
| active      | bool     | False after /withdraw     |

### `items.csv`

| Column        | Type | Notes                        |
|---------------|------|------------------------------|
| id            | str  | e.g. `b1`, `n1`, `item1`    |
| name          | str  |                              |
| starting_price| int  | IDR, no decimals             |
| detail        | str  |                              |
| link          | str  | Online shop URL              |
| active        | bool | Admin flag — exclude from auction if False |

### `bids.csv`

| Column      | Type     | Notes              |
|-------------|----------|--------------------|
| bid_id      | str      | UUID               |
| item_id     | str      | FK → items.csv     |
| telegram_id | int      | FK → users.csv     |
| amount      | int      | IDR, no decimals   |
| timestamp   | datetime | ISO 8601           |
| revoked     | bool     | Default False      |

---

## Bot Commands

### `/participate`

- Registers calling user's `telegram_id` + `username` into `users.csv`
- Idempotent — re-registering reactivates if previously withdrawn
- Group-only

### `/withdraw`

- Sets user `active = False` in `users.csv`
- Marks all their bids `revoked = True` in `bids.csv`
- Group-only, requires active participant

### `/list_items`

- Shows all active auction items (admin `active=True`)
- Displays auction window status (open/closed/not started)
- Per item: starting price, current leading bid with username, full bid history (amounts only)
- Visible to all group members

### `/my_auctions`

- Requires active participant; works in group or DM
- During auction: shows each item the user has bid on, with "leading" or "not leading" status
- After auction ends: shows "WON" or "not won" based on `resolve_at_close` results

### `/bid <item_id> <amount>`

- Only works when auction window is open (`AUCTION_START` ≤ now ≤ `AUCTION_END`)
- Validates: user registered and active, item exists and active, amount > current leading bid, amount ≥ starting_price
- Appends new row to `bids.csv` — full history preserved, old bids not removed

### `/revoke <item_id>`

- Only works when auction window is open
- Marks user's active bid on that item as `revoked = True`

### `/winners`

- Only available after `AUCTION_END`
- Runs `resolve_at_close` and displays final winner per item

### `/help`

- Lists all available commands

---

## Auction Logic

### Auction Window

Controlled globally via environment variables:

```
AUCTION_START=2026-05-08T00:00:00+07:00
AUCTION_END=2026-05-15T23:59:59+07:00
```

- Before `AUCTION_START`: bidding not open
- Between `AUCTION_START` and `AUCTION_END`: bidding open
- After `AUCTION_END`: bidding closed, `/winners` unlocked

### During Auction — Leading Bid

- The user with the current highest non-revoked bid is "leading" per item
- Tie-break: earlier timestamp wins
- "Leading" does not guarantee winning — final results only determined at close

### At Close — resolve_at_close

Each user can win **at most one item**. Applied only after `AUCTION_END`:

```python
def resolve_at_close(items, bids):
    # 1. Sort items by highest top bid (most valuable items assigned first)
    # 2. For each item in order:
    #    a. Get ranked list of non-revoked bidders (highest amount first, earliest timestamp wins tie)
    #    b. Assign to first bidder not already assigned a win
    # 3. Return dict: item_id → winning Bid (or None if no eligible bidder)
```

This ensures no mid-auction lock-outs or cascading state changes — standings are fluid during bidding and only resolved at close.

---

## CSV CRUD Rules

- All reads: load full CSV into memory via `csv.DictReader`
- All writes: append-only for bids; full-rewrite for users/items
- Use `filelock` to prevent race conditions on concurrent updates
- Never delete rows — use soft deletes (`revoked`, `active` flags)

---

## Config (`config.py`)

```python
BOT_TOKEN     = os.environ["BOT_TOKEN"]
GROUP_ID      = int(os.environ["GROUP_ID"])
AUCTION_START = datetime.fromisoformat(os.environ.get("AUCTION_START", ""))  # optional
AUCTION_END   = datetime.fromisoformat(os.environ.get("AUCTION_END", ""))    # optional
DATA_DIR      = Path("data/")
USERS_CSV     = DATA_DIR / "users.csv"
ITEMS_CSV     = DATA_DIR / "items.csv"
BIDS_CSV      = DATA_DIR / "bids.csv"
```

Helper functions: `auction_is_open()`, `auction_has_ended()`

### `.env.example` (committed to repo)

```
BOT_TOKEN=
GROUP_ID=
AUCTION_START=2026-05-08T00:00:00+07:00
AUCTION_END=2026-05-15T23:59:59+07:00
```

Copy to `.env` and fill in values before running. Never commit `.env`.

---

## Access Control Rules

1. All commands except `/participate` and `/help` require `active = True` in `users.csv`
2. All commands must be sent from `GROUP_ID`, except `/my_auctions` which also works in DM
3. `/list_items` shows leading bid username but not `telegram_id`
4. `/my_auctions` filters bids by `telegram_id` — no cross-user data exposure

---

## Error Handling Conventions

| Condition                  | Reply                                                  |
|----------------------------|--------------------------------------------------------|
| User not registered        | `"You're not a participant. Use /participate first."`  |
| Item not found             | `"Item ID not found."`                                 |
| Bid too low                | `"Bid must be higher than current leading: RpX by @Y"` |
| Already revoked            | `"You have no active bid on this item."`               |
| Auction not open           | `"Auction is not currently open for bidding."`         |
| Item inactive              | `"[item_id] name is not available for bidding."`       |
| Winners before close       | `"Auction is still ongoing. Winners will be announced after it ends."` |

All errors reply in the same chat thread — no silent failures.

---

## Development Notes

- Use `async`/`await` throughout — python-telegram-bot v20 is fully async
- Handlers registered in `bot.py` via `Application.add_handler()`
- Keep business logic out of command handlers — handlers call `core/` functions only
- CSV operations in `core/csv_store.py` are the **only** place that touches files
- On first run, `bot.py` auto-creates `data/` dir and empty CSVs with headers
- Run with: `venv/bin/python bot.py` (or `python bot.py` with venv activated)
- Env vars loaded via `python-dotenv` from `.env`
- Virtual environment: `venv/` (gitignored)

### First-time local setup (WSL)

```bash
git clone git@github.com:<you>/auction-bot.git ~/auction-bot
cd ~/auction-bot
python3 -m venv venv          # create virtual environment
source venv/bin/activate      # activate venv
cp .env.example .env          # fill in all values
pip install -r requirements.txt
python bot.py                 # data/ dir auto-created on first run
```

### Adding items (manual)

Edit `data/items.csv` directly. Schema:

```
id,name,starting_price,detail,link,active
b1,Monitor Palsu,200000,Good condition,http://tokped.com,True
```

---

## Out of Scope (for now)

- Admin commands (adding/removing items via bot)
- Web dashboard
- Notifications / push alerts when outbid
- Multi-group support
