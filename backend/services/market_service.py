import requests
import pandas as pd

def get_market_data():

    url = (
        "https://api.coingecko.com/api/v3/coins/markets"
        "?vs_currency=usd"
        "&order=market_cap_desc"
        "&per_page=20"
        "&page=1"
        "&sparkline=false"
        "&price_change_percentage=24h"
    )

    response = requests.get(url)

    data = response.json()

    return pd.DataFrame(data)