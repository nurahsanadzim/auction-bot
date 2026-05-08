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
[b1] Monitor Palsu  — Starting: Rp200.000
[b2] Meja           — Starting: Rp100.000
[n1] Kaos           — Starting: Rp10.000
```

### During the auction

**alice** bids on b1:
```
/bid b1 210000
→ Bid placed: Rp210.000 on [b1] Monitor Palsu
```

**bob** outbids alice on b1:
```
/bid b1 250000
→ Bid placed: Rp250.000 on [b1] Monitor Palsu
```

**alice** checks her status:
```
/my_auctions
→ [b1] Monitor Palsu
     Your bid: Rp210.000 — not leading (leading: Rp250.000)
```

**alice** moves to b2 instead:
```
/bid b2 110000
→ Bid placed: Rp110.000 on [b2] Meja
```

**charlie** bids on b2:
```
/bid b2 120000
→ Bid placed: Rp120.000 on [b2] Meja
```

**bob** also bids on b2:
```
/bid b2 130000
→ Bid placed: Rp130.000 on [b2] Meja
```

**charlie** bids on n1:
```
/bid n1 15000
→ Bid placed: Rp15.000 on [n1] Kutang
```

### `/list_items` mid-auction

```
Auction is OPEN — closes at 2026-05-15 23:59 WIB

[b1] Monitor Palsu
  Starting price: Rp200.000
  Leading: Rp250.000 by @bob

[b2] Meja
  Starting price: Rp100.000
  Leading: Rp130.000 by @bob
  Bid history: Rp130.000, Rp120.000, Rp110.000

[n1] Kutang
  Starting price: Rp10.000
  Leading: Rp15.000 by @charlie
```

### After auction ends — `/winners`

Resolution pass (items sorted by highest bid, most valuable first):

| Item | Top bids in order | Result |
|------|-------------------|--------|
| b1 (Rp250.000) | bob → assigned | **bob wins b1** |
| b2 (Rp130.000) | bob → already won → charlie (Rp120.000) → assigned | **charlie wins b2** |
| n1 (Rp15.000) | charlie → already won → no more bidders | **no winner** |

```
/winners
→ Auction Winners:

[b1] Monitor Palsu  → @bob     — Rp250.000
[b2] Meja           → @charlie — Rp120.000
[n1] Kutang         → No winner
```

---

## Adding Items

Items are managed manually in `data/items.csv`:

```csv
id,name,starting_price,detail,link,active
b1,Monitor Palsu,200000,Good condition,http://tokped.com,True
b2,Meja,100000,Slightly used,http://tokped.com,True
n1,Kutang,10000,Brand new,http://tokped.com,True
```

Set `active=False` to hide an item from the auction without deleting it.
