import requests

def get_crypto_news():

    url = "https://cryptopanic.com/api/v1/posts/?auth_token=demo&public=true"

    response = requests.get(url)

    data = response.json()

    return data.get("results", [])