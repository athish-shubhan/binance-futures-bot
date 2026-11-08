# Binance Futures Testnet — Trading Bot

Python CLI for placing orders on [testnet.binancefuture.com](https://testnet.binancefuture.com).

## Structure

```
core/
  api.py          # signed HTTP client
  trade.py        # order builder
main.py           # argparse CLI
validate.py       # input guards
log.py            # logging setup (writes bot.log)
cli_menu.py       # interactive menu CLI
ui.py             # Flask web UI
requirements.txt
```

This bot only talks to the Binance Futures **testnet** (`testnet.binancefuture.com`); it does not trade real funds.

---

## Setup

```bash
git clone https://github.com/athish-shubhan/binance-futures-bot.git
cd binance-futures-bot
pip install -r requirements.txt
```

Set credentials once (passing `--key` / `--secret` on the command line also works, but they then show up in your shell history and process list):

```bash
export BINANCE_KEY=your_testnet_api_key
export BINANCE_SECRET=your_testnet_secret
```

### Get testnet credentials
1. Visit [testnet.binancefuture.com](https://testnet.binancefuture.com) and sign in with GitHub.
2. Click **API Key** → generate a key pair.

---

## Three Ways to Run

### 1 · Argparse CLI

```bash
# MARKET order
python main.py --symbol BTCUSDT --side BUY --type MARKET --qty 0.001

# LIMIT order
python main.py --symbol BTCUSDT --side SELL --type LIMIT --qty 0.001 --price 99000

# STOP_MARKET order
python main.py --symbol BTCUSDT --side SELL --type STOP_MARKET --qty 0.001 --stop 85000
```

---

### 2 · Interactive menu CLI

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

### 3 · Web UI

```bash
python ui.py
# then open http://127.0.0.1:5000
```

Custom port / host:
```bash
python ui.py --port 8080
```

The UI has no authentication and places orders with the configured API keys, so keep it bound to `127.0.0.1` (the default). Do not expose it with `--host 0.0.0.0` on a shared network.

Features:
- BUY / SELL toggle, dropdown menus, live order summary panel
- Price / stop fields appear/hide based on order type
- Inline validation before the request is sent
- Result panel shows all order fields on success
- Activity log strip at the bottom

---

## Output (argparse CLI)

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
- Supported order types are `MARKET`, `LIMIT` and `STOP_MARKET`.

> **Note on STOP_MARKET:** the testnet `/fapi/v1/order` endpoint can behave differently from the live API.

---
