"""Run the web UI with the exchange call replaced by a canned reply.

Used only to record docs/demo.gif (see scripts/record_demo.js): it lets the
real page, the real validation and the real request handling run without API
keys and without sending anything to Binance. Not for trading.
"""
import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import log  # noqa: E402
import ui  # noqa: E402

_ids = itertools.count(13172225226)


def fake_place(client, symbol, side, otype, qty, price=None, stop=None):
    """Shaped like a testnet /fapi/v1/order reply for a resting order."""
    return {
        "orderId": next(_ids), "symbol": symbol, "status": "NEW", "side": side, "type": otype,
        "origQty": f"{qty:.3f}", "executedQty": "0.000",
        "price": f"{price:.2f}" if price else "0.00", "stopPrice": f"{stop:.2f}" if stop else "0.00",
    }


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5080
    ui.place = fake_place
    ui._log = log.setup("demo.log")
    ui._api_key, ui._api_secret = "demo-key", "demo-secret"
    ui.app.run(host="127.0.0.1", port=port, debug=False)
