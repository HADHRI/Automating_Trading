import json,hmac, hashlib, time, requests, base64
from requests.auth import AuthBase
from conf import conf
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

# Create custom authentication for Exchange
class CoinbaseExchangeAuth(AuthBase):
    def __init__(self, api_key, secret_key, passphrase):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase

    def __call__(self, request):
        timestamp = str(time.time())
        message = timestamp + request.method + request.path_url + (request.body or b'').decode()
        hmac_key = base64.b64decode(self.secret_key)
        signature = hmac.new(hmac_key, message.encode(), hashlib.sha256)
        signature_b64 = base64.b64encode(signature.digest()).decode()

        request.headers.update({
            'CB-ACCESS-SIGN': signature_b64,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        })
        return request

#We will use this in order to request private API 
auth = CoinbaseExchangeAuth(conf['API_KEY'], conf['API_SECRET_KEY'], conf['API_PASS'])

#This API is private , we will use the key in order to request it , otherwise we will be forbidden 403 returned code
def get_book_order_of_asset(asset):
    response = requests.get('https://api-public.sandbox.pro.coinbase.com/products/{}/book'.format(asset), auth=auth) 
    if(response.status_code == 404):
        print("not found , please verify the spelling of the asset ")
        return
    print(response.json())
     
# read agregated trading data (candles)
def refresh_data_candle(pair,duration):
    response = requests.get('https://api-public.sandbox.pro.coinbase.com/products/{}/candles?granularity{}'.format(pair,duration*60), auth=auth)
    if(response.status_code == 404):
        print("not found , please verify the spelling of the asset ")
        return
    print(response.json())




    
    
#Test functions  

#get_all_crypto_currency()
#get_depth('bid','BTC-USD')
#get_book_order_of_asset('BTC-USD')
refresh_data_candle('BTC-USD',5)
