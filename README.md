# Auction Bot

A Telegram bot for running auctions in a group chat. Users register, place bids on items, and winners are resolved fairly after the auction ends — each user can win at most one item.

---

## Setup

```bash
git clone https://github.com/nurahsanadzim/auction-bot.git ~/auction-bot
cd ~/auction-bot
python3 -m venv venv
source venv/bin/activate
cp .env.example .env        # fill in your values
pip install -r requirements.txt
python bot.py
```

### `.env` values

```
BOT_TOKEN=your_telegram_bot_token
GROUP_ID=your_group_chat_id
AUCTION_START=2026-05-08T00:00:00+07:00
AUCTION_END=2026-05-15T23:59:59+07:00
BACKUP_GROUP_ID=your_backup_group_chat_id
```

---

## Commands

| Command | Description |
|---------|-------------|
| `/participate` | Join the auction |
| `/withdraw` | Leave and revoke all your bids |
| `/list_items` | View all items and current leading bids |
| `/my_auctions` | View your bids and status |
| `/bid <item_id> <amount>` | Place a bid on an item |
| `/revoke <item_id>` | Revoke your bid on an item |
| `/winners` | Show final winners (after auction ends) |
| `/help` | List all commands |

---

## How It Works

1. **Register** with `/participate` before the auction opens
2. **Browse items** with `/list_items` to see starting prices and current leaders
3. **Bid** on any item during the auction window — you can bid on multiple items
4. **Track your bids** with `/my_auctions` — shows who is currently leading each item
5. **Winners announced** via `/winners` after the auction ends — each user wins at most one item

> Standings during the auction show who is **leading**, not who has won. Final results are only resolved at close.

---

## Auction Rules

- Each user can win **at most one item**
- The 1-win constraint is enforced **only at close** — you can freely bid on multiple items during the auction
- Winner per item = highest non-revoked bidder who hasn't already won another item
- Tie-break: the bid placed earliest wins
- Items are assigned priority by highest bid value (most expensive item resolved first)

---

## Example: Bidding Between Users

### Items available
```
[1] Monitor  — Starting: Rp200.000
[2] Meja     — Starting: Rp200.000
[3] Gitar    — Starting: Rp200.000
```

### During the auction

**alice** bids on item 1:
```
/bid 1 210000
→ Bid placed: Rp210.000 on [1] Monitor
```

**bob** outbids alice on item 1:
```
/bid 1 250000
→ Bid placed: Rp250.000 on [1] Monitor
```

**alice** checks her status:
```
/my_auctions
→ [1] Monitor
     Your bid: Rp210.000 — not leading (leading: Rp250.000)
```

**alice** moves to item 2 instead:
```
/bid 2 210000
→ Bid placed: Rp210.000 on [2] Meja
```

**bob** also bids on item 2:
```
/bid 2 220000
→ Bid placed: Rp220.000 on [2] Meja
```

**charlie** bids on item 2 and item 3:
```
/bid 2 230000
→ Bid placed: Rp230.000 on [2] Meja

/bid 3 210000
→ Bid placed: Rp210.000 on [3] Gitar
```

### `/list_items` mid-auction

```
Auction is OPEN — closes at 2026-05-20 23:59 WIB

[1] Monitor
  Starting price: Rp200.000
  Leading: Rp250.000 by @bob

[2] Meja
  Starting price: Rp200.000
  Leading: Rp230.000 by @charlie
  Bid history: Rp230.000, Rp220.000, Rp210.000

[3] Gitar
  Starting price: Rp200.000
  Leading: Rp210.000 by @charlie
```

### After auction ends — `/winners`

Resolution pass (items sorted by highest bid, most valuable first):

| Item | Top bids in order | Result |
|------|-------------------|--------|
| 1 Monitor (Rp250.000) | bob → assigned | **bob wins Monitor** |
| 2 Meja (Rp230.000) | charlie → assigned | **charlie wins Meja** |
| 3 Gitar (Rp210.000) | charlie → already won → no more bidders | **no winner** |

```
/winners
→ Auction Winners:

[1] Monitor → @bob     — Rp250.000
[2] Meja    → @charlie — Rp230.000
[3] Gitar   → No winner
```

---

## Adding Items

Items are managed manually in `data/items.csv`:

```csv
id,name,starting_price,detail,link,active
1,Monitor,200000,Good condition,https://tokopedia.com/...,TRUE
2,Meja,200000,Slightly used,https://tokopedia.com/...,TRUE
3,Gitar,200000,Brand new,https://tokopedia.com/...,TRUE
```

Set `active=FALSE` to hide an item from the auction without deleting it.

---

## Backup

A daily backup script (`backup.sh`) tarballs all CSVs in `data/` and sends them to a Telegram backup group.

### Manual run

```bash
chmod +x backup.sh
./backup.sh
```

### Cron setup (runs at 23:50 WIB)

If your server is in **UTC** (default on most VPS):
```
50 16 * * * /home/deploy/auction-bot/backup.sh >> /home/deploy/auction-bot/data/backup.log 2>&1
```

If your server is set to **Asia/Jakarta (WIB)**:
```
50 23 * * * /home/deploy/auction-bot/backup.sh >> /home/deploy/auction-bot/data/backup.log 2>&1
```

Backups are saved to `data/backups/` and logs to `data/backup.log`.

---

## Deployment (DigitalOcean Droplet)

```bash
# On the server
git clone https://github.com/nurahsanadzim/auction-bot.git ~/auction-bot
cd ~/auction-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in all values
chmod +x backup.sh
```

Run as a systemd service:

```ini
# /etc/systemd/system/auction-bot.service
[Unit]
Description=Auction Bot
After=network.target

[Service]
User=deploy
WorkingDirectory=/home/deploy/auction-bot
ExecStart=/home/deploy/auction-bot/venv/bin/python bot.py
Restart=always
RestartSec=5
EnvironmentFile=/home/deploy/auction-bot/.env

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable auction-bot
systemctl start auction-bot
```

### Updating after a push

```bash
cd ~/auction-bot && git pull && sudo systemctl restart auction-bot
```
