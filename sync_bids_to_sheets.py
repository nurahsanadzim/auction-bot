import csv
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import gspread
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(__file__).parent / "data"
USERS_CSV = DATA_DIR / "users.csv"
ITEMS_CSV = DATA_DIR / "items.csv"
BIDS_CSV  = DATA_DIR / "bids.csv"
SPREADSHEET_ID = "15XA1Le7H-4FYgOa4VKxJjS23FMQqRnDQ2LI-MAgUZJA"


def _notify(token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    urllib.request.urlopen(url, data=payload, timeout=10)


def _load_item_map() -> dict[str, str]:
    if not ITEMS_CSV.exists():
        return {}
    with open(ITEMS_CSV, newline="") as f:
        return {r["id"]: r["name"] for r in csv.DictReader(f)}


def _load_username_map() -> dict[int, str]:
    if not USERS_CSV.exists():
        return {}
    with open(USERS_CSV, newline="") as f:
        return {int(r["telegram_id"]): r["username"] for r in csv.DictReader(f)}


def _load_bids() -> tuple[list[str], list[dict]]:
    if not BIDS_CSV.exists():
        return [], []
    with open(BIDS_CSV, newline="") as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames or [])
        rows = list(reader)
    return headers, rows


def main():
    creds = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    gc = gspread.service_account_from_dict(creds)

    ws = gc.open_by_key(SPREADSHEET_ID).sheet1

    item_map    = _load_item_map()
    username_map = _load_username_map()
    headers, rows = _load_bids()

    if not headers:
        print("No bids data found.")
        return

    out_headers = []
    for h in headers:
        if h == "telegram_id":
            out_headers.append("username")
        elif h == "item_id":
            out_headers.append("item_name")
        else:
            out_headers.append(h)
    data = [out_headers]

    for row in rows:
        out_row = []
        for col in headers:
            if col == "telegram_id":
                tid = int(row[col])
                out_row.append(username_map.get(tid, str(tid)))
            elif col == "item_id":
                out_row.append(item_map.get(row[col], row[col]))
            else:
                out_row.append(row[col])
        data.append(out_row)

    ws.clear()
    ws.update("A1", data)

    msg = f"Synced {len(rows)} bids to spreadsheet."
    print(msg)

    token   = os.environ.get("BOT_TOKEN", "")
    chat_id = os.environ.get("GROUP_ID", "")
    if token and chat_id:
        _notify(token, chat_id, f"[Bid Sync] {msg}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
