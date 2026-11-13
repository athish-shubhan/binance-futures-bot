from types import SimpleNamespace

import pytest

import validate


def test_valid_orders_are_normalised():
    assert validate.order(" btcusdt ", "buy", "market", "0.001") == ("BTCUSDT", "BUY", "MARKET", 0.001, None, None)
    assert validate.order("ETHUSDT", "SELL", "LIMIT", 1, price="2500") == ("ETHUSDT", "SELL", "LIMIT", 1.0, 2500.0, None)
    assert validate.order("ETHUSDT", "SELL", "STOP_MARKET", 1, stop=2000) == (
        "ETHUSDT", "SELL", "STOP_MARKET", 1.0, None, 2000.0)


def test_fields_that_do_not_apply_are_dropped():
    # a stray price/stop must not reach the exchange on a MARKET order
    assert validate.order("BTCUSDT", "BUY", "MARKET", 1, price=5, stop=6)[4:] == (None, None)
    assert validate.order("BTCUSDT", "BUY", "LIMIT", 1, price=5, stop=6)[4:] == (5.0, None)


@pytest.mark.parametrize("qty", [None, "", "abc", 0, -1, float("nan"), float("inf"), True, [], {}])
def test_bad_quantity_is_rejected(qty):
    with pytest.raises(ValueError, match="qty"):
        validate.order("BTCUSDT", "BUY", "MARKET", qty)


@pytest.mark.parametrize("price", [None, 0, -5, "x", float("nan")])
def test_limit_needs_a_positive_price(price):
    with pytest.raises(ValueError, match="price"):
        validate.order("BTCUSDT", "BUY", "LIMIT", 1, price=price)


@pytest.mark.parametrize("stop", [None, 0, -5, "x", float("inf")])
def test_stop_market_needs_a_positive_stop(stop):
    with pytest.raises(ValueError, match="stop"):
        validate.order("BTCUSDT", "SELL", "STOP_MARKET", 1, stop=stop)


@pytest.mark.parametrize("symbol", ["", None, "BT", "BTC/USDT", "BTC USDT"])
def test_bad_symbol_is_rejected(symbol):
    with pytest.raises(ValueError, match="symbol"):
        validate.order(symbol, "BUY", "MARKET", 1)


def test_bad_side_and_type_are_rejected():
    with pytest.raises(ValueError, match="side"):
        validate.order("BTCUSDT", "HOLD", "MARKET", 1)
    with pytest.raises(ValueError, match="type"):
        validate.order("BTCUSDT", "BUY", "TRAILING", 1)


def test_run_normalises_a_namespace_in_place():
    a = SimpleNamespace(symbol="btcusdt", side="BUY", type="LIMIT", qty="2", price="10", stop=3)
    validate.run(a)
    assert (a.symbol, a.type, a.qty, a.price, a.stop) == ("BTCUSDT", "LIMIT", 2.0, 10.0, None)


def test_run_accepts_a_namespace_without_symbol_or_side():
    a = SimpleNamespace(type="MARKET", qty=1, price=None, stop=None)
    validate.run(a)
    assert a.qty == 1.0
