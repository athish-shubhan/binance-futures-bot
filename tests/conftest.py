import logging

import pytest


class FakeResponse:
    def __init__(self, status=200, payload=None, text=None):
        self.status_code = status
        self._payload = payload
        self.text = text if text is not None else str(payload)

    @property
    def ok(self):
        return self.status_code < 400

    def json(self):
        if self._payload is None:
            raise ValueError("no JSON body")
        return self._payload


class FakeSession:
    """Stands in for requests.Session: records calls, returns a canned response."""

    def __init__(self, response=None):
        self.headers = {}
        self.calls = []
        self.response = response or FakeResponse(payload={"orderId": 1, "status": "NEW"})

    def post(self, url, **kw):
        self.calls.append((url, kw))
        return self.response


@pytest.fixture
def log():
    return logging.getLogger("bot-test")


@pytest.fixture
def client(log):
    from core.api import Client

    c = Client("test-key", "test-secret", log)
    c.sess = FakeSession()
    return c
