def place(c, sym, side, otype, qty, price=None, stop=None):
    p = {"symbol": sym, "side": side, "type": otype, "quantity": qty}
    if otype == "LIMIT":
        p.update({"price": price, "timeInForce": "GTC"})
    if otype == "STOP_MARKET":
        p["stopPrice"] = stop
    return c.post("/fapi/v1/order", p)
