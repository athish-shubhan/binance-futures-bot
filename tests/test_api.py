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
