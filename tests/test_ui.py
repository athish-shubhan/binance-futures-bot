import logging

import pytest

import ui


@pytest.fixture
def web(monkeypatch):
    placed = []

    def fake_place(c, *args):
        placed.append(args)
        return {"orderId": 42, "status": "NEW"}

    monkeypatch.setattr(ui, "place", fake_place)
    monkeypatch.setattr(ui, "_log", logging.getLogger("bot-test"))
    monkeypatch.setattr(ui, "_api_key", "k")
    monkeypatch.setattr(ui, "_api_secret", "s")
    ui.app.config["TESTING"] = True
    return ui.app.test_client(), placed


def test_index_serves_the_page(web):
    c, _ = web
    r = c.get("/")
    assert r.status_code == 200 and b"<html" in r.data


def test_valid_order_is_placed_with_normalised_fields(web):
    c, placed = web
    r = c.post("/api/order", json={"symbol": "btcusdt", "side": "buy", "type": "limit", "qty": "0.5", "price": 100})
    assert r.get_json() == {"success": True, "result": {"orderId": 42, "status": "NEW"}}
    assert placed == [("BTCUSDT", "BUY", "LIMIT", 0.5, 100.0, None)]


@pytest.mark.parametrize("payload", [
    {"symbol": "BTCUSDT", "side": "BUY", "type": "MARKET", "qty": None},   # empty field -> NaN -> null
    {"symbol": "BTCUSDT", "side": "BUY", "type": "MARKET", "qty": "abc"},
    {"symbol": "BTCUSDT", "side": "BUY", "type": "LIMIT", "qty": 1, "price": None},
    {"symbol": "BTCUSDT", "side": "BUY", "type": "STOP_MARKET", "qty": 1, "stop": -1},
    {"symbol": "", "side": "BUY", "type": "MARKET", "qty": 1},
    {"symbol": "BTCUSDT", "side": "HOLD", "type": "MARKET", "qty": 1},
    {},
])
def test_invalid_order_returns_json_error_and_is_not_sent(web, payload):
    c, placed = web
    r = c.post("/api/order", json=payload)
    body = r.get_json()
    assert body["success"] is False and body["error"]
    assert placed == []


@pytest.mark.parametrize("raw", [b"not json", b"[1, 2]", b'"text"', b""])
def test_malformed_body_is_a_400_json_error(web, raw):
    c, placed = web
    r = c.post("/api/order", data=raw, content_type="application/json")
    assert r.status_code == 400
    assert r.get_json()["success"] is False
    assert placed == []
