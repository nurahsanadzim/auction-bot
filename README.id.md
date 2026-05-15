# Auction Bot

Bot Telegram untuk menjalankan lelang di grup chat. Peserta mendaftar, memasang bid pada barang yang diinginkan, dan pemenang ditentukan setelah lelang berakhir — setiap peserta hanya bisa menang satu barang.

---

## Setup

```bash
git clone https://github.com/nurahsanadzim/auction-bot.git ~/auction-bot
cd ~/auction-bot
python3 -m venv venv
source venv/bin/activate
cp .env.example .env        # isi nilai-nilainya
pip install -r requirements.txt
python bot.py
```

### Nilai di file `.env`

```
BOT_TOKEN=token_bot_telegram_kamu
GROUP_ID=id_grup_telegram_kamu
AUCTION_START=2026-05-08T00:00:00+07:00
AUCTION_END=2026-05-20T23:59:59+07:00
BACKUP_GROUP_ID=id_grup_backup_kamu
```

---

## Perintah Bot

| Perintah | Keterangan |
|----------|------------|
| `/participate` | Daftar ikut lelang |
| `/withdraw` | Keluar dan batalkan semua bid kamu |
| `/list_items` | Lihat semua barang dan bid tertinggi saat ini |
| `/my_auctions` | Lihat status bid kamu |
| `/bid <item_id> <jumlah>` | Pasang bid pada suatu barang |
| `/revoke <item_id>` | Batalkan bid kamu di suatu barang |
| `/winners` | Lihat pemenang lelang (setelah lelang selesai) |
| `/rules` | Lihat aturan lelang |
| `/help` | Tampilkan daftar perintah |

---

## Cara Kerjanya

1. **Daftar** dengan `/participate` sebelum lelang dimulai
2. **Lihat barang** dengan `/list_items` — ada harga awal dan siapa yang sedang leading
3. **Pasang bid** di barang manapun selama lelang berlangsung — boleh bid lebih dari satu barang
4. **Pantau bid kamu** dengan `/my_auctions` — terlihat siapa yang sedang unggul di tiap barang
5. **Pemenang diumumkan** lewat `/winners` setelah lelang tutup — satu orang maksimal menang satu barang

> Status "leading" selama lelang bukan berarti sudah menang. Hasil final baru ditentukan saat lelang tutup.

---

## Aturan Lelang

- Setiap peserta hanya bisa **menang satu barang**
- Aturan 1 kemenangan ini baru berlaku **saat lelang tutup** — selama lelang berlangsung, bebas bid di barang manapun
- Semua nominal bid harus **kelipatan Rp20.000** (misal Rp200.000, Rp220.000, Rp240.000)
- Pemenang per barang = bidder tertinggi yang belum menang barang lain
- Jika ada bid yang sama, yang lebih awal dipasang yang menang
- Barang dengan bid tertinggi diprioritaskan lebih dulu saat penentuan pemenang

---

## Contoh Lelang

### Barang yang tersedia
```
[1] Monitor  — Mulai: Rp200.000
[2] Meja     — Mulai: Rp200.000
[3] Gitar    — Mulai: Rp200.000
```

### Selama lelang berlangsung

**alice** bid barang 1:
```
/bid 1 200000
→ Bid placed: Rp200.000 on [1] Monitor
```

**bob** mengungguli alice di barang 1:
```
/bid 1 220000
→ Bid placed: Rp220.000 on [1] Monitor
```

**alice** cek statusnya:
```
/my_auctions
→ [1] Monitor
     Your bid: Rp200.000 — not leading (leading: Rp220.000)
```

**alice** pindah ke barang 2:
```
/bid 2 200000
→ Bid placed: Rp200.000 on [2] Meja
```

**bob** ikut bid barang 2:
```
/bid 2 220000
→ Bid placed: Rp220.000 on [2] Meja
```

**charlie** bid barang 2 dan 3:
```
/bid 2 240000
→ Bid placed: Rp240.000 on [2] Meja

/bid 3 200000
→ Bid placed: Rp200.000 on [3] Gitar
```

### `/list_items` di tengah lelang

```
Auction is OPEN — closes at 2026-05-20 23:59 WIB

[1] Monitor
  Starting price: Rp200.000
  Leading: Rp220.000 by @bob

[2] Meja
  Starting price: Rp200.000
  Leading: Rp240.000 by @charlie
  Bid history: Rp240.000, Rp220.000, Rp200.000

[3] Gitar
  Starting price: Rp200.000
  Leading: Rp200.000 by @charlie
```

### Setelah lelang tutup — `/winners`

Urutan penentuan pemenang (barang dengan bid tertinggi diproses lebih dulu):

| Barang | Urutan bid | Hasil |
|--------|------------|-------|
| 2 Meja (Rp240.000) | charlie → dapat | **charlie menang Meja** |
| 1 Monitor (Rp220.000) | bob → dapat | **bob menang Monitor** |
| 3 Gitar (Rp200.000) | charlie → sudah menang → tidak ada bidder lain | **tidak ada pemenang** |

```
/winners
→ Auction Winners:

[1] Monitor → @bob     — Rp220.000
[2] Meja    → @charlie — Rp240.000
[3] Gitar   → No winner
```

---

## Menambah Barang

Barang dikelola langsung lewat file `data/items.csv`:

```csv
id,name,starting_price,detail,link,active
1,Monitor,200000,Kondisi bagus,https://tokopedia.com/...,TRUE
2,Meja,200000,Bekas sedikit,https://tokopedia.com/...,TRUE
3,Gitar,200000,Baru,https://tokopedia.com/...,TRUE
```

Set `active=FALSE` untuk menyembunyikan barang tanpa menghapusnya.
- `starting_price` harus kelipatan 20000

---

## Backup

Script `backup.sh` berjalan otomatis setiap hari — mengarsipkan semua file CSV di `data/` dan mengirimnya ke grup Telegram backup.

### Jalankan manual

```bash
chmod +x backup.sh
./backup.sh
```

### Setup Cron (setiap hari jam 23:50 WIB)

Kalau server menggunakan **UTC** (default di kebanyakan VPS):
```
50 16 * * * /home/deploy/auction-bot/backup.sh >> /home/deploy/auction-bot/data/backup.log 2>&1
```

Kalau server sudah diset ke **Asia/Jakarta (WIB)**:
```
50 23 * * * /home/deploy/auction-bot/backup.sh >> /home/deploy/auction-bot/data/backup.log 2>&1
```

Hasil backup tersimpan di `data/backups/`, log tersimpan di `data/backup.log`.

---

## Deploy (DigitalOcean Droplet)

```bash
# Di server
git clone https://github.com/nurahsanadzim/auction-bot.git ~/auction-bot
cd ~/auction-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # isi semua nilainya
chmod +x backup.sh
```

Jalankan sebagai systemd service supaya otomatis aktif kembali saat server restart:

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

### Update setelah push

```bash
cd ~/auction-bot && git pull && sudo systemctl restart auction-bot
```
