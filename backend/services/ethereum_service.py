import requests

RPC_URL = "https://eth.llamarpc.com"

def get_latest_block():
    payload = {
        "jsonrpc":"2.0",
        "method":"eth_blockNumber",
        "params":[],
        "id":1
    }

    response = requests.post(RPC_URL, json=payload)

    return response.json()