import os
import sys
import argparse
import requests

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    _RC = True
except ImportError:
    _RC = False

try:
    import questionary
    from questionary import Style as QStyle
    _Q = True
except ImportError:
    _Q = False

from log import setup
from core.api import Client
from core.trade import place
import validate as _validate

cn = Console() if _RC else None

_QS = QStyle([
    ("qmark",        "fg:#00d7af bold"),
    ("question",     "bold"),
    ("answer",       "fg:#00d7af bold"),
    ("pointer",      "fg:#00d7af bold"),
    ("highlighted",  "fg:#00d7af bold"),
    ("selected",     "fg:#00d7af"),
    ("separator",    "fg:#555555"),
    ("instruction",  "fg:#777777"),
]) if _Q else None


def _pr(mg, st=""):
    if _RC:
        cn.print(mg, style=st)
    else:
        print(mg)

def _as(pt, cs):
    if _Q:
        return questionary.select(pt, choices=cs, style=_QS).ask()
    print(f"\n{pt}")
    for i, c in enumerate(cs, 1):
        print(f"  {i}. {c}")
    while True:
        rw = input("  Choice [number]: ").strip()
        if rw.isdigit() and 1 <= int(rw) <= len(cs):
            return cs[int(rw) - 1]
        print("  ✗ Invalid choice, try again.")

def _at(pt, vf=None, df=""):
    ht = f" [{df}]" if df else ""
    while True:
        if _Q:
            rw = questionary.text(pt + ht, default=df, style=_QS).ask()
        else:
            rw = input(f"  {pt}{ht}: ").strip() or df
        if rw is None:
            sys.exit("\nAborted.")
        rw = rw.strip()
        if vf:
            try:
                vf(rw)
                return rw
            except (ValueError, AssertionError) as e:
                _pr(f"  ✗  {e}", st="bold red")
        else:
            return rw

def _af(pt, rq=False):
    while True:
        if _Q:
            rw = questionary.text(pt, style=_QS).ask()
        else:
            rw = input(f"  {pt}: ").strip()
        if rw is None:
            sys.exit("\nAborted.")
        rw = rw.strip()
        if not rw:
            if not rq:
                return None
            _pr("  ✗  This field is required.", st="bold red")
            continue
        try:
            vl = float(rw)
            if vl <= 0:
                raise ValueError("Must be > 0")
            return vl
        except ValueError as e:
            _pr(f"  ✗  {e}", st="bold red")


def _ss(sy, sd, ot, qt, pc, sp):
    tg = f"@ {pc}" if pc else (f"stop @ {sp}" if sp else "at market")
    if _RC:
        cn.print()
        cn.rule("[bold cyan]Order Request[/bold cyan]")
        tb = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        tb.add_column(style="dim")
        tb.add_column(style="bold white")
        tb.add_row("Symbol",   sy)
        tb.add_row("Side",     f"[green]{sd}[/green]" if sd == "BUY" else f"[red]{sd}[/red]")
        tb.add_row("Type",     ot)
        tb.add_row("Quantity", str(qt))
        tb.add_row("Price",    tg)
        cn.print(tb)
        cn.rule()
    else:
        print(f"\n{'─'*44}")
        print(f"  {ot} {sd}  {qt} {sy}  {tg}")
        print(f"{'─'*44}")


def _sr(rs):
    fd = ["orderId", "status", "executedQty", "avgPrice", "price",
          "stopPrice", "type", "side", "origQty", "cumQuote"]
    if _RC:
        cn.print()
        cn.rule("[bold green]✓  Order Placed[/bold green]")
        tb = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        tb.add_column(style="dim")
        tb.add_column(style="bold white")
        for f in fd:
            if f in rs:
                tb.add_row(f, str(rs[f]))
        cn.print(tb)
        cn.rule()
    else:
        print("\n✓  Order placed")
        for f in fd:
            if f in rs:
                print(f"  {f:<14}: {rs[f]}")
        print()


def interactive(ak, sk, lg):
    if _RC:
        cn.print(Panel.fit(
            "[bold cyan]Binance Futures Testnet[/bold cyan]\n"
            "[dim]Interactive Order Placer[/dim]",
            border_style="cyan"
        ))
    else:
        print("\n=== Binance Futures Testnet — Interactive Order Placer ===\n")

    cm = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "Other (type manually)"]
    sc = _as("Select symbol:", cm)
    if sc.startswith("Other"):
        sy = _at(
            "Enter symbol",
            vf=lambda v: (_ for _ in ()).throw(ValueError("Symbol too short")) if len(v) < 3 else None,
        ).upper()
    else:
        sy = sc

    sd = _as("Side:", ["BUY", "SELL"])
    ot = _as("Order type:", ["MARKET", "LIMIT", "STOP_MARKET"])
    qt = _af("Quantity (e.g. 0.001 for BTC)", rq=True)

    pc = None
    sp = None
    if ot == "LIMIT":
        pc = _af("Limit price  (e.g. 99000)", rq=True)
    elif ot == "STOP_MARKET":
        sp = _af("Stop trigger price  (e.g. 85000)", rq=True)

    class _Ar:
        pass
    ar = _Ar()
    ar.qty   = qt
    ar.type  = ot
    ar.price = pc
    ar.stop  = sp

    try:
        _validate.run(ar)
    except ValueError as e:
        _pr(f"\n✗  Validation error: {e}", st="bold red")
        sys.exit(1)

    _ss(sy, sd, ot, qt, pc, sp)

    if _Q:
        ok = questionary.confirm("Place this order?", style=_QS, default=True).ask()
    else:
        ok = input("Place this order? [Y/n]: ").strip().lower() not in ("n", "no")

    if not ok:
        _pr("\nCancelled.", st="dim")
        sys.exit(0)

    try:
        cl  = Client(ak, sk, lg)
        rs  = place(cl, sy, sd, ot, qt, pc, sp)
        lg.info(f"Order placed: {rs}")
        _sr(rs)
    except requests.exceptions.HTTPError as e:
        bd = getattr(e, "api_msg", None) or (e.response.json() if e.response else {})
        lg.error(f"API error: {bd}")
        _pr(f"\n✗  [{bd.get('code')}] {bd.get('msg', str(e))}", st="bold red")
        sys.exit(1)
    except Exception as e:
        lg.error(f"Failed: {e}")
        _pr(f"\n✗  {e}", st="bold red")
        sys.exit(1)

    if _Q:
        ag = questionary.confirm("Place another order?", style=_QS, default=False).ask()
    else:
        ag = input("\nPlace another order? [y/N]: ").strip().lower() in ("y", "yes")

    if ag:
        interactive(ak, sk, lg)


def main():
    pp = argparse.ArgumentParser(
        prog="cli_menu",
        description="Binance Futures Testnet — interactive menu-driven CLI",
    )
    pp.add_argument("--key",    default=os.getenv("BINANCE_KEY"),    help="API key")
    pp.add_argument("--secret", default=os.getenv("BINANCE_SECRET"), help="API secret")
    av = pp.parse_args()

    lg = setup()

    if not av.key or not av.secret:
        sys.exit(
            "\n✗  API credentials missing.\n"
            "   Set BINANCE_KEY / BINANCE_SECRET env vars, or use --key / --secret.\n"
        )

    interactive(av.key, av.secret, lg)


if __name__ == "__main__":
    main()
