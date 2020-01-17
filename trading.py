import requests
import json
#get list of all availables cryptocurrencies and display it 
def get_all_crypto_currency():
    url = 'https://rest.coinapi.io/v1/assets'
    response = requests.get(url)
    print(json.dumps(response.json()))

get_all_crypto_currency()
