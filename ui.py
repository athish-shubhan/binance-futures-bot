"""
ui.py  —  Lightweight Flask web UI for the Binance Futures bot.

Run:  python ui.py
      BINANCE_KEY=xxx BINANCE_SECRET=yyy python ui.py
      python ui.py --key xxx --secret yyy

Opens at http://127.0.0.1:5000
"""

import os
import sys
import argparse
import requests as _req
from urllib.parse import urlsplit
from flask import Flask, request, jsonify

# local modules
from log import setup
from core.api import Client
from core.trade import place
import validate as _validate

app = Flask(__name__)
_log = None
_api_key = None
_api_secret = None
_hosts = {"127.0.0.1", "localhost"}   # Host names this UI answers to

# ─────────────────────────────────────────────────────────────────────────────
#  HTML (single-page app, all CSS + JS inline)
# ─────────────────────────────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Binance Futures Bot</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

  :root {
    --bg:       #0d0f14;
    --surface:  #13161e;
    --border:   #1f2433;
    --accent:   #00d7af;
    --accent2:  #0090ff;
    --red:      #ff4d6a;
    --green:    #00d7af;
    --text:     #e2e8f0;
    --muted:    #64748b;
    --radius:   8px;
    --mono:     'IBM Plex Mono', monospace;
    --sans:     'IBM Plex Sans', sans-serif;
  }

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--sans);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  /* ── header ── */
  header {
    width: 100%;
    padding: 18px 32px;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 14px;
  }
  .logo {
    width: 34px; height: 34px;
    background: var(--accent);
    border-radius: 6px;
    display: grid; place-items: center;
    font-family: var(--mono);
    font-weight: 600;
    font-size: 14px;
    color: #000;
  }
  header h1 { font-size: 15px; font-weight: 600; letter-spacing: .03em; }
  header p  { font-size: 12px; color: var(--muted); margin-top: 2px; }
  .pill {
    margin-left: auto;
    background: #0a2a20;
    border: 1px solid var(--accent);
    color: var(--accent);
    font-family: var(--mono);
    font-size: 11px;
    padding: 4px 12px;
    border-radius: 100px;
  }

  /* ── layout ── */
  main {
    width: 100%;
    max-width: 880px;
    padding: 36px 20px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
  }
  @media (max-width: 640px) { main { grid-template-columns: 1fr; } }

  /* ── card ── */
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 24px;
  }
  .card-title {
    font-family: var(--mono);
    font-size: 11px;
    font-weight: 600;
    letter-spacing: .12em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 20px;
  }

  /* ── form elements ── */
  .field { margin-bottom: 16px; }
  label {
    display: block;
    font-size: 12px;
    font-weight: 600;
    color: var(--muted);
    margin-bottom: 6px;
    letter-spacing: .04em;
    text-transform: uppercase;
  }
  input, select {
    width: 100%;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    font-family: var(--mono);
    font-size: 14px;
    padding: 10px 14px;
    outline: none;
    transition: border-color .15s;
    appearance: none;
  }
  input:focus, select:focus { border-color: var(--accent); }
  input::placeholder { color: var(--muted); }
  select option { background: var(--surface); }

  /* ── side toggle ── */
  .toggle-group {
    display: flex;
    gap: 8px;
  }
  .toggle-group button {
    flex: 1;
    padding: 10px;
    border-radius: 6px;
    border: 1px solid var(--border);
    background: var(--bg);
    color: var(--muted);
    font-family: var(--mono);
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: all .15s;
  }
  .toggle-group button.active-buy  { background: #0a2a20; border-color: var(--green); color: var(--green); }
  .toggle-group button.active-sell { background: #2a0a14; border-color: var(--red);   color: var(--red); }

  /* ── submit button ── */
  #submit-btn {
    width: 100%;
    padding: 13px;
    background: var(--accent);
    color: #000;
    font-family: var(--mono);
    font-size: 14px;
    font-weight: 600;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    letter-spacing: .04em;
    margin-top: 4px;
    transition: opacity .15s;
  }
  #submit-btn:hover    { opacity: .85; }
  #submit-btn:disabled { opacity: .4; cursor: not-allowed; }
  #submit-btn.loading::after {
    content: ' ···';
    animation: dots 1s infinite;
  }
  @keyframes dots {
    0%,100% { opacity: 0 }
    50%      { opacity: 1 }
  }

  /* ── result panel ── */
  .result-panel {
    grid-column: 1 / -1;
    display: none;
  }
  .result-panel.show { display: block; }

  .result-inner {
    border-radius: var(--radius);
    border: 1px solid var(--border);
    overflow: hidden;
  }

  .result-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 14px 20px;
    font-family: var(--mono);
    font-size: 13px;
    font-weight: 600;
  }
  .result-header.success { background: #0a2a20; color: var(--green); }
  .result-header.error   { background: #2a0a14; color: var(--red); }

  .result-body {
    background: var(--surface);
    padding: 20px;
  }

  .kv-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 14px;
  }
  .kv { }
  .kv .k {
    font-size: 11px;
    font-family: var(--mono);
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: .06em;
    margin-bottom: 3px;
  }
  .kv .v {
    font-family: var(--mono);
    font-size: 15px;
    font-weight: 600;
    color: var(--text);
    word-break: break-all;
  }

  .error-msg {
    font-family: var(--mono);
    font-size: 13px;
    color: var(--red);
  }

  /* ── log panel ── */
  .log-panel {
    grid-column: 1 / -1;
  }
  #log-box {
    font-family: var(--mono);
    font-size: 11px;
    line-height: 1.7;
    color: var(--muted);
    max-height: 160px;
    overflow-y: auto;
    padding: 4px 0;
  }
  #log-box .log-entry { display: block; }
  #log-box .ts  { color: #334155; margin-right: 6px; }
  #log-box .ok  { color: var(--green); }
  #log-box .err { color: var(--red); }
  #log-box .inf { color: var(--accent2); }

  /* ── price conditional ── */
  #price-row, #stop-row { transition: opacity .2s; }
  #price-row.hidden, #stop-row.hidden { opacity: 0; pointer-events: none; height: 0; overflow: hidden; margin: 0; }

  /* ── validation hint ── */
  .hint { font-size: 11px; color: var(--red); margin-top: 4px; display: none; }
  .hint.show { display: block; }
</style>
</head>
<body>

<header>
  <div class="logo">BF</div>
  <div>
    <h1>Binance Futures Bot</h1>
    <p>USDT-M Testnet Order Placer</p>
  </div>
  <span class="pill">TESTNET</span>
</header>

<main>

  <!-- ── Order Form ── -->
  <div class="card">
    <div class="card-title">Place Order</div>

    <div class="field">
      <label>Symbol</label>
      <select id="symbol-select" onchange="onSymbolChange()">
        <option value="BTCUSDT">BTCUSDT</option>
        <option value="ETHUSDT">ETHUSDT</option>
        <option value="SOLUSDT">SOLUSDT</option>
        <option value="BNBUSDT">BNBUSDT</option>
        <option value="custom">Custom…</option>
      </select>
    </div>
    <div class="field" id="custom-symbol-row" style="display:none">
      <label>Custom Symbol</label>
      <input id="custom-symbol" type="text" placeholder="e.g. XRPUSDT" autocomplete="off"/>
      <div class="hint" id="hint-symbol">Symbol must be letters/digits, min 3 chars.</div>
    </div>

    <div class="field">
      <label>Side</label>
      <div class="toggle-group">
        <button id="btn-buy"  onclick="setSide('BUY')"  class="active-buy">▲ BUY</button>
        <button id="btn-sell" onclick="setSide('SELL')" >▼ SELL</button>
      </div>
    </div>

    <div class="field">
      <label>Order Type</label>
      <select id="order-type" onchange="onTypeChange()">
        <option value="MARKET">MARKET</option>
        <option value="LIMIT">LIMIT</option>
        <option value="STOP_MARKET">STOP_MARKET</option>
      </select>
    </div>

    <div class="field">
      <label>Quantity</label>
      <input id="qty" type="number" step="any" min="0" placeholder="0.001"/>
      <div class="hint" id="hint-qty">Quantity must be a positive number.</div>
    </div>

    <div class="field" id="price-row">
      <label>Limit Price</label>
      <input id="price" type="number" step="any" min="0" placeholder="99000"/>
      <div class="hint" id="hint-price">Price must be a positive number.</div>
    </div>

    <div class="field hidden" id="stop-row">
      <label>Stop Trigger Price</label>
      <input id="stop" type="number" step="any" min="0" placeholder="85000"/>
      <div class="hint" id="hint-stop">Stop price must be a positive number.</div>
    </div>

    <button id="submit-btn" onclick="submitOrder()">PLACE ORDER</button>
  </div>

  <!-- ── Order Summary ── -->
  <div class="card" id="summary-card">
    <div class="card-title">Order Summary</div>
    <div id="summary-table" style="font-family:var(--mono);font-size:13px;line-height:2;">
      <div style="color:var(--muted);font-size:12px;margin-top:8px;">Fill the form and place an order to see details here.</div>
    </div>
  </div>

  <!-- ── Result ── -->
  <div class="result-panel" id="result-panel">
    <div class="result-inner">
      <div class="result-header" id="result-header"></div>
      <div class="result-body" id="result-body"></div>
    </div>
  </div>

  <!-- ── Activity Log ── -->
  <div class="card log-panel">
    <div class="card-title">Activity Log</div>
    <div id="log-box"><span style="color:var(--muted);font-size:11px;">No activity yet.</span></div>
  </div>

</main>

<script>
let _side = 'BUY';

function setSide(s) {
  _side = s;
  document.getElementById('btn-buy').className  = s === 'BUY'  ? 'active-buy'  : '';
  document.getElementById('btn-sell').className = s === 'SELL' ? 'active-sell' : '';
  updateSummary();
}

function onSymbolChange() {
  const v = document.getElementById('symbol-select').value;
  document.getElementById('custom-symbol-row').style.display = v === 'custom' ? 'block' : 'none';
  updateSummary();
}

function onTypeChange() {
  const t = document.getElementById('order-type').value;
  document.getElementById('price-row').classList.toggle('hidden', t !== 'LIMIT');
  document.getElementById('stop-row').classList.toggle('hidden', t !== 'STOP_MARKET');
  updateSummary();
}

function getSymbol() {
  const sel = document.getElementById('symbol-select').value;
  return sel === 'custom' ? document.getElementById('custom-symbol').value.trim().toUpperCase() : sel;
}

function updateSummary() {
  const sym   = getSymbol();
  const otype = document.getElementById('order-type').value;
  const qty   = document.getElementById('qty').value;
  const price = document.getElementById('price').value;
  const stop  = document.getElementById('stop').value;
  const sideColor = _side === 'BUY' ? '#00d7af' : '#ff4d6a';

  let priceStr = '—';
  if (otype === 'LIMIT' && price)       priceStr = `@ ${price}`;
  else if (otype === 'STOP_MARKET' && stop) priceStr = `stop @ ${stop}`;
  else if (otype === 'MARKET')          priceStr = 'at market';

  document.getElementById('summary-table').innerHTML = `
    <div><span style="color:var(--muted);width:90px;display:inline-block">Symbol</span><b>${sym || '—'}</b></div>
    <div><span style="color:var(--muted);width:90px;display:inline-block">Side</span><b style="color:${sideColor}">${_side}</b></div>
    <div><span style="color:var(--muted);width:90px;display:inline-block">Type</span><b>${otype}</b></div>
    <div><span style="color:var(--muted);width:90px;display:inline-block">Quantity</span><b>${qty || '—'}</b></div>
    <div><span style="color:var(--muted);width:90px;display:inline-block">Price</span><b>${priceStr}</b></div>
  `;
}

function addLog(msg, cls='') {
  const box = document.getElementById('log-box');
  const ts  = new Date().toLocaleTimeString();
  const el  = document.createElement('span');
  el.className = `log-entry ${cls}`;
  el.innerHTML = `<span class="ts">${ts}</span>${msg}`;
  if (box.firstChild && box.firstChild.textContent.includes('No activity')) box.innerHTML = '';
  box.insertBefore(el, box.firstChild);
}

function showHint(id, show) {
  document.getElementById(id).classList.toggle('show', show);
}

function validate() {
  let ok = true;
  const sym  = getSymbol();
  const otype = document.getElementById('order-type').value;
  const qty   = parseFloat(document.getElementById('qty').value);
  const price = parseFloat(document.getElementById('price').value);
  const stop  = parseFloat(document.getElementById('stop').value);

  const symOk = sym && sym.length >= 3 && /^[A-Z0-9]+$/.test(sym);
  showHint('hint-symbol', !symOk);
  if (!symOk) ok = false;

  const qtyOk = qty > 0;
  showHint('hint-qty', !qtyOk);
  if (!qtyOk) ok = false;

  if (otype === 'LIMIT') {
    const pOk = price > 0;
    showHint('hint-price', !pOk);
    if (!pOk) ok = false;
  }
  if (otype === 'STOP_MARKET') {
    const sOk = stop > 0;
    showHint('hint-stop', !sOk);
    if (!sOk) ok = false;
  }
  return ok;
}

async function submitOrder() {
  // Whatever result is on screen must belong to this submission, so clear the old one first.
  document.getElementById('result-panel').classList.remove('show');
  if (!validate()) return;

  const btn   = document.getElementById('submit-btn');
  const otype = document.getElementById('order-type').value;
  const payload = {
    symbol: getSymbol(),
    side:   _side,
    type:   otype,
    qty:    parseFloat(document.getElementById('qty').value),
    price:  otype === 'LIMIT'       ? parseFloat(document.getElementById('price').value) : null,
    stop:   otype === 'STOP_MARKET' ? parseFloat(document.getElementById('stop').value)  : null,
  };

  btn.disabled = true;
  btn.classList.add('loading');
  btn.textContent = 'PLACING ORDER';

  addLog(`Sending ${payload.type} ${payload.side} ${payload.qty} ${payload.symbol}…`, 'inf');

  try {
    const resp = await fetch('/api/order', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await resp.json();

    const panel  = document.getElementById('result-panel');
    const header = document.getElementById('result-header');
    const body   = document.getElementById('result-body');
    panel.classList.add('show');

    if (data.success) {
      const r = data.result;
      header.className = 'result-header success';
      header.innerHTML = '✓ &nbsp;Order Placed Successfully';
      const fields = [
        ['Order ID',      r.orderId],
        ['Status',        r.status],
        ['Symbol',        r.symbol],
        ['Side',          r.side],
        ['Type',          r.type],
        ['Orig Qty',      r.origQty],
        ['Executed Qty',  r.executedQty],
        ['Avg Price',     r.avgPrice],
        ['Limit Price',   r.price !== '0.00' ? r.price : null],
        ['Stop Price',    r.stopPrice !== '0.00' ? r.stopPrice : null],
        ['Client OID',    r.clientOrderId],
      ].filter(([,v]) => v != null && v !== '');
      body.innerHTML = '<div class="kv-grid">' +
        fields.map(([k,v]) => `<div class="kv"><div class="k">${k}</div><div class="v">${v}</div></div>`).join('') +
        '</div>';
      addLog(`✓ orderId=${r.orderId} status=${r.status}`, 'ok');
    } else {
      header.className = 'result-header error';
      header.innerHTML = '✗ &nbsp;Order Failed';
      body.innerHTML   = `<div class="error-msg">${data.error}</div>`;
      addLog(`✗ ${data.error}`, 'err');
    }
  } catch (e) {
    addLog(`✗ Network error: ${e}`, 'err');
  }

  btn.disabled = false;
  btn.classList.remove('loading');
  btn.textContent = 'PLACE ORDER';
}

// live summary update
['symbol-select','custom-symbol','order-type','qty','price','stop']
  .forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('input', updateSummary);
  });

onTypeChange();   // hide price/stop on load
updateSummary();  // populate summary on load
</script>
</body>
</html>
"""


# ─────────────────────────────────────────────────────────────────────────────
#  Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return HTML


def _trusted_request():
    """True only for requests made by this UI's own page (or a local script).

    The UI has no login and holds the API keys, so without this check any web
    page open in the same browser could place orders by POSTing to
    127.0.0.1. Three independent guards:
      - JSON content type: an HTML form cannot send it, and cross-origin
        JavaScript has to pass a CORS preflight first, which is never granted;
      - Origin, when the browser sends one, must be this server;
      - Host must be a name we serve, which blocks DNS rebinding.
    """
    if request.mimetype != "application/json":
        return False
    if (request.host or "").rsplit(":", 1)[0] not in _hosts:
        return False
    origin = request.headers.get("Origin")
    return origin is None or urlsplit(origin).netloc == request.host


@app.route("/api/order", methods=["POST"])
def api_order():
    if not _trusted_request():
        _log.warning(f"Rejected cross-site request from Origin={request.headers.get('Origin')!r}")
        return jsonify({"success": False, "error": "cross-site request rejected"}), 403

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"success": False, "error": "request body must be a JSON object"}), 400

    # ── server-side validation (the browser checks are only a convenience) ────
    try:
        symbol, side, otype, qty, price, stop = _validate.order(
            data.get("symbol"), data.get("side"), data.get("type"),
            data.get("qty"), data.get("price"), data.get("stop"),
        )
    except ValueError as e:
        _log.error(f"Validation error: {e}")
        return jsonify({"success": False, "error": str(e)})

    try:
        c   = Client(_api_key, _api_secret, _log)
        res = place(c, symbol, side, otype, qty, price, stop)
        _log.info(f"Web UI order placed: {res}")
        return jsonify({"success": True, "result": res})
    except _req.exceptions.HTTPError as e:
        body = getattr(e, "api_msg", None) or {}
        _log.error(f"API error: {body}")
        return jsonify({"success": False, "error": f"[{body.get('code')}] {body.get('msg', str(e))}"})
    except Exception as e:
        _log.error(f"Unexpected error: {e}")
        return jsonify({"success": False, "error": str(e)})


# ─────────────────────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    global _log, _api_key, _api_secret

    p = argparse.ArgumentParser(
        prog="ui",
        description="Binance Futures Testnet — web UI",
    )
    p.add_argument("--key",    default=os.getenv("BINANCE_KEY"))
    p.add_argument("--secret", default=os.getenv("BINANCE_SECRET"))
    p.add_argument("--host",   default="127.0.0.1")
    p.add_argument("--port",   default=5000, type=int)
    a = p.parse_args()

    if not a.key or not a.secret:
        sys.exit(
            "\n✗  API credentials missing.\n"
            "   Set BINANCE_KEY / BINANCE_SECRET env vars, or use --key / --secret.\n"
        )

    _log        = setup()
    _api_key    = a.key
    _api_secret = a.secret
    _hosts.add(a.host)

    print("\n  Binance Futures Bot — Web UI")
    print(f"  Open → http://{a.host}:{a.port}\n")
    app.run(host=a.host, port=a.port, debug=False)


if __name__ == "__main__":
    main()
