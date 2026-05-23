# Binance Futures Testnet — Trading Bot

Zero-dependency-bloat Python CLI for placing orders on [testnet.binancefuture.com](https://testnet.binancefuture.com).

## Structure

```
internbot/
  core/
    api.py          # signed HTTP client          [original]
    trade.py        # order builder               [original]
  main.py           # original argparse CLI       [original]
  validate.py       # input guards                [original]
  log.py            # logging setup               [original]
  cli_menu.py       # ★ interactive menu CLI      [added]
  ui.py             # ★ Flask web UI              [added]
  bot.log           # written at runtime
  requirements.txt
```

> **What changed:** Only two files added (`cli_menu.py`, `ui.py`) and `requirements.txt` updated.
> All original files are **untouched**.

---

## Setup

```bash
git clone <repo>
cd internbot
pip install -r requirements.txt
```

Set credentials once (or pass inline with `--key` / `--secret`):

```bash
export BINANCE_KEY=your_testnet_api_key
export BINANCE_SECRET=your_testnet_secret
```

### Get testnet credentials
1. Visit [testnet.binancefuture.com](https://testnet.binancefuture.com) and sign in with GitHub.
2. Click **API Key** → generate a key pair.

---

## Three Ways to Run

### 1 · Original CLI (argparse, unchanged)

```bash
# MARKET order
python main.py --symbol BTCUSDT --side BUY --type MARKET --qty 0.001

# LIMIT order
python main.py --symbol BTCUSDT --side SELL --type LIMIT --qty 0.001 --price 99000

# STOP_MARKET order (bonus)
python main.py --symbol BTCUSDT --side SELL --type STOP_MARKET --qty 0.001 --stop 85000
```

---

### 2 · ★ Interactive Menu CLI (bonus)

```bash
python cli_menu.py
```

Arrow-key menus guide you through symbol → side → type → qty → price.
Validation errors appear inline; a confirmation prompt fires before the order is sent.
Uses `rich` for coloured output and `questionary` for menus — falls back to plain `input()` if either is missing.

```
❯ Select symbol:          BTCUSDT / ETHUSDT / … / Custom
❯ Side:                   BUY / SELL
❯ Order type:             MARKET / LIMIT / STOP_MARKET
❯ Quantity:               0.001
❯ Limit price:            99000       ← only shown for LIMIT
❯ Place this order? [Y/n]

  ────────────────────────────────────
  ✓  Order Placed
     Order ID     : 13172225226
     Status       : NEW
     Orig Qty     : 0.0010
  ────────────────────────────────────
```

---

### 3 · ★ Web UI (bonus)

```bash
python ui.py
# then open http://127.0.0.1:5000
```

Custom port / host:
```bash
python ui.py --port 8080 --host 0.0.0.0
```

Features:
- BUY / SELL toggle, dropdown menus, live order summary panel
- Price / stop fields appear/hide based on order type
- Inline validation before the request is sent
- Result panel shows all order fields on success
- Activity log strip at the bottom

---

## Output (original CLI)

```
────────────────────────────────────────────
  LIMIT SELL  0.001 BTCUSDT  @ 99000.0
────────────────────────────────────────────

✓  Order placed
  orderId       : 13172225226
  status        : NEW
  executedQty   : 0.0000
  price         : 99000.00
  type          : LIMIT
  side          : SELL
```

All API requests, responses, and errors are written to `bot.log`.

---

## Assumptions

- Only USDT-M futures pairs (e.g. `BTCUSDT`, `ETHUSDT`).
- Quantity precision must match the symbol's lot size — use `0.001` for BTC.
- `STOP_MARKET` is the bonus third order type; no extra dependencies needed.

> **Note on STOP_MARKET:** The Futures Testnet `/fapi/v1/order` endpoint has
> known limitations vs. the live API. Implementation matches the live API spec.

---

## Notes on AI Assistance

Parts of this project were vibe-coded with AI help:

- **Web UI** (`ui.py`) — the frontend HTML/CSS/JS was largely AI-assisted. The Python Flask wiring, API integration, and backend logic were written manually.
- **README** — drafted with AI assistance and edited for accuracy.
- **Interactive CLI** - A Basic CLI was done and enhanced with AI for design
- All core bot logic (`core/api.py`, `core/trade.py`, `validate.py`, `log.py`, `main.py`) was written without AI help.
