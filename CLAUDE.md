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
│   ├── list_big.py
│   ├── list_normal.py
│   ├── my_auctions.py
│   ├── participate.py
│   ├── withdraw.py
│   ├── bid.py
│   └── revoke.py
├── data/                   # ⚠ gitignored — local only
│   ├── users.csv           # Registered participants
│   ├── items.csv           # Auction items
│   └── bids.csv            # All bid records
├── core/
│   ├── csv_store.py        # CRUD abstraction for CSV
│   ├── auction_logic.py    # Big/normal auction rules
│   └── models.py           # Dataclasses: User, Item, Bid
├── config.py               # BOT_TOKEN, GROUP_ID, paths
├── .env                    # ⚠ gitignored — secrets only
├── .env.example            # committed — template with empty values
├── .gitignore
├── requirements.txt
└── CLAUDE.md
```

---

## Data Models

### `users.csv`

| Column      | Type     | Notes              |
|-------------|----------|--------------------|
| telegram_id | int      | Primary key        |
| username    | str      | @handle            |
| joined_at   | datetime | ISO 8601           |
| active      | bool     | False after /withdraw |

### `items.csv`

| Column        | Type   | Notes                    |
|---------------|--------|--------------------------|
| id            | str    | e.g. `b1`, `b2` (big), `n1`, `n2` (normal) |
| name          | str    |                          |
| type          | enum   | `big` or `normal`        |
| starting_price| int    | IDR, no decimals         |
| detail        | str    |                          |
| link          | str    | Online shop URL          |
| active        | bool   |                          |

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
- Idempotent — re-registering does nothing
- Only works inside the configured group

### `/withdraw`

- Sets user `active = False` in `users.csv`
- Marks all their bids `revoked = True` in `bids.csv`
- Triggers re-evaluation of big auction winners

### `/list-big`

- Shows all active big auction items
- Format per item: `[ID] Name — Current top: Rp9.000 (Anonymous)`
- Includes full bid history per item, all names shown as Anonymous

### `/list-normal`

- Same as `/list-big` but for normal items

### `/my-auctions`

- Only works for registered participants
- Shows user's own bids per item, with win status
- Win status logic differs by auction type (see below)

### `/bid <item_id> <amount>`

- Validates: user registered, item exists and active, amount > current top bid, amount >= starting_price
- Appends new row to `bids.csv`
- Does NOT replace old bids — full history preserved

### `/revoke <item_id>`

- Marks user's active bid on that item as `revoked = True`
- Triggers re-evaluation if they were top bidder

---

## Auction Logic

### Normal Auction

- Top non-revoked bid per item wins
- A user can win multiple items
- Winner = user with highest active bid

### Big Auction

- Each user can only win **one** item
- Algorithm:
  1. For each item, find top non-revoked bid → tentative winner
  2. If a user is tentative winner on multiple items → they keep only the **highest-priced** win
  3. For items they "vacate", promote the next highest non-revoked bidder
  4. Re-run until no conflicts (iterative resolution)
- This re-evaluation runs on every `/bid`, `/revoke`, and `/withdraw`

### Big Auction Re-evaluation (pseudologic)

```python
def resolve_big_auction(items, bids):
    # 1. Get top active bid per item
    # 2. Build user -> [items won] map
    # 3. For users with >1 win: keep max(amount), release others
    # 4. For released items: get next top bidder, repeat from step 2
    # until stable (no user wins >1 item)
```

---

## CSV CRUD Rules

- All reads: load full CSV into memory (`pandas` or `csv.DictReader`)
- All writes: append-only for bids; full-rewrite for users/items
- Use file locking (`fcntl` / `filelock` lib) to prevent race conditions on concurrent updates
- Never delete rows — use soft deletes (`revoked`, `active` flags)

---

## Config (`config.py`)

```python
BOT_TOKEN = os.environ["BOT_TOKEN"]
GROUP_ID  = int(os.environ["GROUP_ID"])   # Restrict commands to this group
DATA_DIR  = Path("data/")
USERS_CSV = DATA_DIR / "users.csv"
ITEMS_CSV = DATA_DIR / "items.csv"
BIDS_CSV  = DATA_DIR / "bids.csv"
```

### `.env.example` (committed to repo)

```
BOT_TOKEN=
GROUP_ID=
```

Copy to `.env` and fill in values before running. Never commit `.env`.

---

## Access Control Rules

1. All commands except `/participate` require the user to be in `users.csv` with `active = True`
2. All commands must be sent from `GROUP_ID` (or optionally allow `/my-auctions` in DM)
3. `/my-auctions` filters bids by `telegram_id` — no cross-user data exposure
4. `/list-big` and `/list-normal` never expose `telegram_id` or username

---

## Error Handling Conventions

| Condition              | Reply                                              |
|------------------------|----------------------------------------------------|
| User not registered    | `"You're not a participant. Use /participate first."` |
| Item not found         | `"Item ID not found."`                             |
| Bid too low            | `"Bid must be higher than current top: RpX"`       |
| Already revoked        | `"You have no active bid on this item."`           |

All errors reply in the same chat thread — no silent failures.

---

## Development Notes

- Use `async`/`await` throughout — python-telegram-bot v20 is fully async
- Handlers registered in `bot.py` via `Application.add_handler()`
- Keep business logic out of command handlers — handlers call `core/` functions only
- CSV operations in `core/csv_store.py` should be the **only** place that touches files
- On first run, `bot.py` must auto-create `data/` dir and empty CSVs with headers if not present
- Run with: `venv/bin/python bot.py` (or `python bot.py` with venv activated)
- Env vars loaded via `python-dotenv` from `.env`
- Virtual environment: `venv/` (gitignored)

### First-time local setup (WSL)

```bash
git clone git@github.com:<you>/auction-bot.git ~/auction-bot
cd ~/auction-bot
python3 -m venv venv          # create virtual environment
source venv/bin/activate      # activate venv
cp .env.example .env          # fill in BOT_TOKEN and GROUP_ID
pip install -r requirements.txt
python bot.py                 # data/ dir auto-created on first run
```

---

## Out of Scope (for now)

- Admin commands (adding items, closing auction rounds)
- Web dashboard
- Notifications / push alerts when outbid
- Multi-group support