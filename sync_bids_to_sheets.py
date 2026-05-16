import csv
import json
import os
import sys
from pathlib import Path

import gspread
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(__file__).parent / "data"
USERS_CSV = DATA_DIR / "users.csv"
BIDS_CSV  = DATA_DIR / "bids.csv"
SPREADSHEET_ID = "15XA1Le7H-4FYgOa4VKxJjS23FMQqRnDQ2LI-MAgUZJA"


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

    username_map = _load_username_map()
    headers, rows = _load_bids()

    if not headers:
        print("No bids data found.")
        return

    out_headers = [("username" if h == "telegram_id" else h) for h in headers]
    data = [out_headers]

    for row in rows:
        out_row = []
        for col in headers:
            if col == "telegram_id":
                tid = int(row[col])
                out_row.append(username_map.get(tid, str(tid)))
            else:
                out_row.append(row[col])
        data.append(out_row)

    ws.clear()
    ws.update("A1", data)
    print(f"Synced {len(rows)} bids to spreadsheet.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
