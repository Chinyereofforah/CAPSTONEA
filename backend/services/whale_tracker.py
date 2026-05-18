import requests

def get_whale_transactions():

    url = "https://api.whale-alert.io/v1/transactions"

    return requests.get(url).json()