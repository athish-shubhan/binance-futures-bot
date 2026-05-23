import argparse, os, sys, requests
from log import setup
from core.api import Client
from core.trade import place
import validate

def fmt_order(res):
    fields = ["orderId", "status", "executedQty", "avgPrice", "price", "stopPrice", "type", "side"]
    lines = [f"  {f:<14}: {res[f]}" for f in fields if f in res]
    return "\n".join(lines)

def main():
    p = argparse.ArgumentParser(prog="bot", description="Binance Futures Testnet — order placer")
    p.add_argument("--key",    default=os.getenv("BINANCE_KEY"),    help="API key (or set BINANCE_KEY)")
    p.add_argument("--secret", default=os.getenv("BINANCE_SECRET"), help="API secret (or set BINANCE_SECRET)")
    p.add_argument("--symbol", required=True,                        help="e.g. BTCUSDT")
    p.add_argument("--side",   required=True, choices=["BUY","SELL"])
    p.add_argument("--type",   required=True, choices=["MARKET","LIMIT","STOP_MARKET"])
    p.add_argument("--qty",    required=True, type=float)
    p.add_argument("--price",  type=float,    help="Limit price (LIMIT orders)")
    p.add_argument("--stop",   type=float,    help="Stop trigger price (STOP_MARKET orders)")
    a = p.parse_args()

    log = setup()

    try:
        if not a.key or not a.secret:
            raise ValueError("API credentials missing — use --key/--secret or env vars BINANCE_KEY/BINANCE_SECRET")
        validate.run(a)

        c = Client(a.key, a.secret, log)
        tag = f"@ {a.price}" if a.price else (f"stop @ {a.stop}" if a.stop else "at market")
        print(f"\n{'─'*44}")
        print(f"  {a.type} {a.side}  {a.qty} {a.symbol}  {tag}")
        print(f"{'─'*44}")

        res = place(c, a.symbol, a.side, a.type, a.qty, a.price, a.stop)
        log.info(f"Order placed: {res}")
        print(f"\n✓  Order placed\n{fmt_order(res)}\n")

    except ValueError as e:
        log.error(f"Validation: {e}")
        sys.exit(f"\n✗  {e}\n")
    except requests.exceptions.HTTPError as e:
        body = getattr(e, 'api_msg', None) or (e.response.json() if e.response else {})
        log.error(f"API error: {body}")
        sys.exit(f"\n✗  [{body.get('code')}] {body.get('msg', str(e))}\n")
    except Exception as e:
        log.error(f"Failed: {e}")
        sys.exit(f"\n✗  {e}\n")

if __name__ == "__main__":
    main()
