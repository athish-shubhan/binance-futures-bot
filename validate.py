import math

SIDES = ("BUY", "SELL")
TYPES = ("MARKET", "LIMIT", "STOP_MARKET")


def _num(v, name, required=True):
    """Coerce v to a positive finite float. None/"" means "not given"."""
    if v is None or v == "":
        if required:
            raise ValueError(f"{name} is required")
        return None
    if isinstance(v, bool):
        raise ValueError(f"{name} must be a number")
    try:
        f = float(v)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a number") from None
    if not math.isfinite(f):
        raise ValueError(f"{name} must be a finite number")
    if f <= 0:
        raise ValueError(f"{name} must be > 0")
    return f


def order(symbol, side, otype, qty, price=None, stop=None):
    """Validate one order and return it normalised as
    (symbol, side, type, qty, price, stop).

    Raises ValueError with a message that is safe to show to the user.
    Fields that do not apply to the order type are returned as None, so a
    stray --price on a MARKET order is never sent to the exchange.
    """
    symbol = str(symbol or "").strip().upper()
    if len(symbol) < 3 or not symbol.isalnum():
        raise ValueError("symbol must be letters/digits, e.g. BTCUSDT")
    side = str(side or "").strip().upper()
    if side not in SIDES:
        raise ValueError(f"side must be one of {', '.join(SIDES)}")
    otype = str(otype or "").strip().upper()
    if otype not in TYPES:
        raise ValueError(f"type must be one of {', '.join(TYPES)}")
    qty = _num(qty, "qty")
    price = _num(price, "price", required=otype == "LIMIT") if otype == "LIMIT" else None
    stop = _num(stop, "stop", required=otype == "STOP_MARKET") if otype == "STOP_MARKET" else None
    return symbol, side, otype, qty, price, stop


def run(a):
    """Validate an argparse-style namespace in place (qty, type, price, stop,
    and symbol/side when present)."""
    sym, side, otype, qty, price, stop = order(
        getattr(a, "symbol", "BTCUSDT"), getattr(a, "side", "BUY"), a.type, a.qty,
        getattr(a, "price", None), getattr(a, "stop", None),
    )
    if hasattr(a, "symbol"):
        a.symbol = sym
    if hasattr(a, "side"):
        a.side = side
    a.type, a.qty, a.price, a.stop = otype, qty, price, stop
