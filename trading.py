import json,hmac, hashlib, time, requests, base64
from requests.auth import AuthBase
from conf import conf
import sqlite3
from sqlite3 import Error
from datetime import datetime
from dateutil import parser




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
     


#let's create a connection with the SQLITE Table

def create_connection_sqlite(db_file):
    try :
        conn =sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

conn=create_connection_sqlite("sql_file.db")

#print(conn)
connection = conn.cursor()
print(connection)
##The code in order to create SQLITE table if not exists
#Create the last_checks table , this table will hold the last_check when we update other tables for example , we add a line in this table 
connection.execute('''CREATE TABLE IF NOT EXISTS last_checks(Id INTEGER PRIMARY KEY, exchange TEXT, trading_pair TEXT, duration TEXT, table_name TEXT, last_check INT, startdate INT,last_id INT)''')
#Create candle table
#first example with pair=BTC-USD and duration =5
exchange_name='CoinBase'
pair='BTC-USD'
#5 minutes 
duration=5 
#print(pair.replace('-','_'))

set_table_name = str(exchange_name + "_" + pair.replace('-','_') + "_"+ str(duration))
table_creation_statement = '''CREATE TABLE IF NOT EXISTS '''+set_table_name + '''(Id INTEGER PRIMARY KEY, date INT, high REAL, low REAL, open REAL, close REAL,volume REAL)'''
#print(table_creation_statement) 
connection.execute(table_creation_statement)
#print(connection)  

# read agregated trading data (candles)
#Pair is the name of the asset
#Duration is in minutes 
def refresh_data_candle(pair,duration):
    response = requests.get('https://api-public.sandbox.pro.coinbase.com/products/{}/candles?granularity{}'.format(pair,duration*60), auth=auth)
    if(response.status_code == 404):
        print("not found , please verify the spelling of the asset ")
        return
    #store data in the candle table 
    #get Table Name 
    set_table_name = str(exchange_name + "_" + pair.replace('-','_') + "_"+ str(duration))
    table_creation_statement = '''CREATE TABLE IF NOT EXISTS '''+set_table_name + '''(Id INTEGER PRIMARY KEY, date INT, high REAL, low REAL, open REAL, close REAL,volume REAL)'''
    connection.execute(table_creation_statement)
    res=response.json()
    #Update table only if candle data is available
    #get last day from specific candle table and then compare it
    last_date=1 
    last_date = connection.execute('''SELECT date FROM ''' +  set_table_name + ''' ORDER BY date DESC LIMIT 1''').fetchone() 
    if(res[0][0] == last_date):
        return
    for var in response.json():
        #print(var)
        sql = ''' INSERT INTO '''+set_table_name+'''(date,high,low,open,close,volume) VALUES(?,?,?,?,?,?)'''
        connection.execute(sql,[var[0], var[2], var[1], var[3], var[4], var[5]])
    last_id = connection.lastrowid
    #Adding the information that we have updated this table to LAST_check table
    
    #last date inserted in the pair table 
    #print(res[len(res)-1][0])
    last_day=res[len(res)-1][0]
    connection.execute('''INSERT INTO last_checks(exchange,trading_pair,duration,table_name,last_check,startdate,last_id)
            VALUES(?,?,?,?,?,?,?)''',[exchange_name, pair, duration,  set_table_name, datetime.now(), last_day, last_id])
 
    


# get all available trade data for an asset
def refresh_data(pair):
    response = requests.get('https://api-public.sandbox.pro.coinbase.com/products/{}/trades'.format(pair), auth=auth)
    if(response.status_code == 404):
        print("not found ")
        return
    setTableName = str(exchange_name + "_" +  pair.replace('-','_'))
    table_creation_statement =  '''CREATE TABLE IF NOT EXISTS ''' +setTableName + '''(Id INTEGER PRIMARY KEY, uuid TEXT, traded_btc REAL, price REAL, created_at_int INT, side TEXT)'''
    connection.execute(table_creation_statement)
    res=response.json()
    for var in response.json():
        #print(var)
        sql = '''INSERT INTO ''' +  setTableName +'''(uuid,traded_btc,price,created_at_int,side) VALUES (?,?,?,?,?)'''
        connection.execute(sql,[var.get('trace_id'), var.get('size'), var.get('price'),datetime.timestamp(parser.isoparse(var.get('time'))), var.get('side')])
    last_id = connection.lastrowid
    # insert in last check table 
    last_day=res[len(res)-1]['time']
    connection.execute('''INSERT INTO last_checks(exchange,trading_pair,duration,table_name,last_check,startdate,last_id) VALUES(?,?,?,?,?,?,?)''',[exchange_name, pair, 0, setTableName, datetime.now(), datetime.timestamp(parser.isoparse(last_day)), last_id])


# Task List Post to REST API
# I put BTC-USD As default pair and Limit order as limite type default value 
def create_order(direction,price,amount,pair = 'BTC-USD', orderType = 'limit'):
     # construct the json to send 
    send_value = {
    'side': direction,
    'price': price,
    'size': amount,
    'product_id': pair,
    'type': orderType
    }
    response = requests.post('https://api-public.sandbox.pro.coinbase.com/orders',json=send_value, auth=auth)
    if(response.status_code == 404):
        print("Something went worng ")
        return
    print(response.json())


# Post http with providing order id  in order to cancel an order 
def cancel_order(id):
    res = requests.post('https://api-public.sandbox.pro.coinbase.com/orders{}'.format(id), auth=auth)
    return res.json()


 







#Test functions  with examples

#get_all_crypto_currency()
#get_depth('bid','BTC-USD')
#get_book_order_of_asset('BTC-USD')
#refresh_data_candle('BTC-USD',5)
#refresh_data('BTC-USD')

#verify that data are inserted in table of BTC_USD  with select * query 
#for var in connection.execute('''SELECT * FROM ''' + set_table_name ):
    #print(var)

#full_data_set="CoinBase_BTC_USD"
#verify that data are inserted in full data set
#for var in connection.execute('''SELECT * FROM ''' + full_data_set ):
    #print(var)


#POST TASK LIST 
#create_order('sell',0.20000000,0.10000000) # I want to test it , I think it works but I don't have enough funds 
cancel_order(2)