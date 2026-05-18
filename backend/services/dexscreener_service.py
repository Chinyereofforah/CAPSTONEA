import requests

def get_pair_data(pair_address):

    url = f"https://api.dexscreener.com/latest/dex/pairs/ethereum/{pair_address}"

    response = requests.get(url)

    return response.json()