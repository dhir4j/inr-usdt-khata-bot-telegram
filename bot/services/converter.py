def inr_to_usdt(amount_inr: float, price: float) -> float:
    if price <= 0:
        return 0
    return round(amount_inr / price, 2)


def usdt_to_inr(amount_usdt: float, price: float) -> float:
    return round(amount_usdt * price, 2)


def convert_amount(amount: float, currency: str, price: float) -> tuple[float, float]:
    """Returns (amount_inr, amount_usdt) regardless of input currency."""
    currency = currency.lower()
    if currency == "inr":
        return round(amount, 2), inr_to_usdt(amount, price)
    else:
        return usdt_to_inr(amount, price), round(amount, 2)
