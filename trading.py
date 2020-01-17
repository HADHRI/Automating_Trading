import requests
import json
#get list of all availables cryptocurrencies and display it 
def get_all_crypto_currency():
    url = 'https://rest.coinapi.io/v1/assets'
    response = requests.get(url)
    print(json.dumps(response.json()))


def get_depth(direction, pair):
    url_coinBase_pro='https://api.pro.coinbase.com/products/{}/ticker'.format(pair)
    response = requests.get(url_coinBase_pro)
    if(response.status_code == 404):
        print("not found , please verify the spelling of the asset . for example BTC-USD and not BTCUSD")
        return
    if(direction =='ask'):
        print(response.json()['ask'])
    elif direction == 'bid':
        print(response.json()['bid'])
    else:
        #I print all if there's a problem with the direction input 
        print(response.json())
        
    
    
#Test functions 

#get_all_crypto_currency()
get_depth('bid','BTC-USD')

