def run(a):
    if a.qty <= 0:
        raise ValueError("qty must be > 0")
    if a.type == "LIMIT" and not a.price:
        raise ValueError("--price required for LIMIT orders")
    if a.price and a.price <= 0:
        raise ValueError("price must be > 0")
    if a.type == "STOP_MARKET" and not a.stop:
        raise ValueError("--stop required for STOP_MARKET orders")
