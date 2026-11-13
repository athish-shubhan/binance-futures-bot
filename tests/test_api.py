import hashlib
import hmac
from urllib.parse import urlencode

import pytest
import requests

from core.api import URL
from tests.conftest import FakeResponse


def test_api_key_is_sent_as_header(log):
    from core.api import Client

    c = Client("test-key", "test-secret", log)
    assert c.sess.headers["X-MBX-APIKEY"] == "test-key"


def test_request_is_signed_with_hmac_sha256(client):
    client.post("/fapi/v1/order", {"symbol": "BTCUSDT", "side": "BUY"})
    url, kw = client.sess.calls[0]
    assert url == f"{URL}/fapi/v1/order"
    sent = dict(kw["params"])
    sig = sent.pop("signature")
    assert "timestamp" in sent
    expected = hmac.new(b"test-secret", urlencode(sent).encode(), hashlib.sha256).hexdigest()
    assert sig == expected


def test_only_testnet_is_targeted():
    assert URL == "https://testnet.binancefuture.com"


def test_api_error_carries_binance_code_and_message(client):
    client.sess.response = FakeResponse(400, {"code": -1121, "msg": "Invalid symbol."})
    with pytest.raises(requests.exceptions.HTTPError) as ei:
        client.post("/fapi/v1/order", {"symbol": "NOPE"})
    assert ei.value.api_msg == {"code": -1121, "msg": "Invalid symbol."}


def test_non_json_error_body_is_kept_as_message(client):
    client.sess.response = FakeResponse(502, None, text="<html>Bad Gateway</html>")
    with pytest.raises(requests.exceptions.HTTPError) as ei:
        client.post("/fapi/v1/order", {})
    assert ei.value.api_msg == {"msg": "<html>Bad Gateway</html>"}


def test_every_request_has_a_timeout(client):
    client.post("/fapi/v1/order", {"symbol": "BTCUSDT"})
    assert client.sess.calls[0][1]["timeout"] == 10


def test_small_quantities_are_not_sent_in_scientific_notation(client):
    client.post("/fapi/v1/order", {"quantity": 0.00001, "price": 99000.0, "stopPrice": 1e-7})
    sent = client.sess.calls[0][1]["params"]
    assert sent["quantity"] == "0.00001"
    assert sent["price"] == "99000.0"
    assert sent["stopPrice"] == "0.0000001"


def test_signature_covers_the_formatted_values(client):
    client.post("/fapi/v1/order", {"quantity": 0.00001})
    sent = dict(client.sess.calls[0][1]["params"])
    sig = sent.pop("signature")
    assert sig == hmac.new(b"test-secret", urlencode(sent).encode(), hashlib.sha256).hexdigest()


def test_caller_params_are_not_mutated_and_none_is_dropped(client):
    p = {"symbol": "BTCUSDT", "price": None}
    client.post("/fapi/v1/order", p)
    assert p == {"symbol": "BTCUSDT", "price": None}
    assert "price" not in client.sess.calls[0][1]["params"]
