import hashlib
import hmac
import time
from decimal import Decimal
from urllib.parse import urlencode

import requests

URL = "https://testnet.binancefuture.com"
TIMEOUT = 10  # seconds; without one a stalled connection hangs the CLI forever


def _fmt(v):
    """Render numbers in plain decimal notation.

    str(0.00001) is '1e-05', which Binance rejects as an illegal quantity.
    """
    if isinstance(v, float):
        return format(Decimal(repr(v)), "f")
    return v


class Client:
    def __init__(self, k, sec, log, timeout=TIMEOUT):
        self.k = k
        self.sec = sec
        self.log = log
        self.timeout = timeout
        self.sess = requests.Session()
        self.sess.headers["X-MBX-APIKEY"] = k

    def _sign(self, p):
        """Return a signed copy of p; the caller's dict is left untouched."""
        p = {k: _fmt(v) for k, v in p.items() if v is not None}
        p["timestamp"] = int(time.time() * 1000)
        q = urlencode(p)
        p["signature"] = hmac.new(self.sec.encode(), q.encode(), hashlib.sha256).hexdigest()
        return p

    def post(self, path, p):
        self.log.debug(f"POST {path} params={p}")
        r = self.sess.post(f"{URL}{path}", params=self._sign(p), timeout=self.timeout)
        self.log.debug(f"Response {r.status_code} body={r.text}")
        if not r.ok:
            e = requests.exceptions.HTTPError(response=r)
            try:
                e.api_msg = r.json()
            except ValueError:
                e.api_msg = {"msg": r.text}
            raise e
        return r.json()
