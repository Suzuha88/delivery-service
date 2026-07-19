# если бы было больше бизнесс логики в приложении можно было бы вывести
# в отдельный слой, но ради одной функции будто бы нет смысла
def calculate_delivery_price(
        item_price_in_dollars: float,
        exchange_rate: float,
        weight: float) -> float:
    return weight * 0.5 + item_price_in_dollars * exchange_rate
