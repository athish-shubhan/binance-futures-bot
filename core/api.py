import time, hmac, hashlib, requests
from urllib.parse import urlencode

URL = "https://testnet.binancefuture.com"

class Client:
    def __init__(self, k, sec, log):
        self.k = k
        self.sec = sec
        self.log = log
        self.sess = requests.Session()
        self.sess.headers["X-MBX-APIKEY"] = k

    def _sign(self, p):
        p["timestamp"] = int(time.time() * 1000)
        q = urlencode(p)
        p["signature"] = hmac.new(self.sec.encode(), q.encode(), hashlib.sha256).hexdigest()
        return p

    def post(self, path, p):
        self.log.debug(f"POST {path} params={p}")
        r = self.sess.post(f"{URL}{path}", params=self._sign(p))
        self.log.debug(f"Response {r.status_code} body={r.text}")
        if not r.ok:
            e = requests.exceptions.HTTPError(response=r)
            try:
                e.api_msg = r.json()
            except ValueError:
                e.api_msg = {"msg": r.text}
            raise e
        return r.json()
