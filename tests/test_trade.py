from core.trade import place


class Recorder:
    def __init__(self):
        self.sent = None

    def post(self, path, params):
        self.sent = (path, params)
        return {"orderId": 7}


def test_market_order_has_no_price_fields():
    c = Recorder()
    assert place(c, "BTCUSDT", "BUY", "MARKET", 0.001) == {"orderId": 7}
    path, p = c.sent
    assert path == "/fapi/v1/order"
    assert p == {"symbol": "BTCUSDT", "side": "BUY", "type": "MARKET", "quantity": 0.001}


def test_limit_order_adds_price_and_gtc():
    c = Recorder()
    place(c, "BTCUSDT", "SELL", "LIMIT", 0.001, price=99000.0)
    p = c.sent[1]
    assert p["price"] == 99000.0
    assert p["timeInForce"] == "GTC"
    assert "stopPrice" not in p


def test_stop_market_order_adds_stop_price_only():
    c = Recorder()
    place(c, "BTCUSDT", "SELL", "STOP_MARKET", 0.001, stop=85000.0)
    p = c.sent[1]
    assert p["stopPrice"] == 85000.0
    assert "price" not in p and "timeInForce" not in p
