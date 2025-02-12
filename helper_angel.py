#DISCLAIMER:
#1) This sample code is for learning purposes only.
#2) Always be very careful when dealing with codes in which you can place orders in your account.
#3) The actual results may or may not be similar to backtested results. The historical results do not guarantee any profits or losses in the future.
#4) You are responsible for any losses/profits that occur in your account in case you plan to take trades in your account.
#5) TFU and Aseem Singhal do not take any responsibility of you running these codes on your account and the corresponding profits and losses that might occur.
#6) The running of the code properly is dependent on a lot of factors such as internet, broker, what changes you have made, etc. So it is always better to keep checking the trades as technology error can come anytime.
#7) This is NOT a tip providing service/code.
#8) This is NOT a software. Its a tool that works as per the inputs given by you.
#9) Slippage is dependent on market conditions.
#10) Option trading and automatic API trading are subject to market risks

#from SmartWebsocketv2 import SmartWebSocketV2
#from smartapi import SmartConnect    #Use SmartApi instead of smartapi if you get error
# try:
#     from SmartApi import SmartConnect    #Use SmartApi instead of smartapi if you get error
#     from SmartApi.smartWebSocketV2 import SmartWebSocketV2
# except:
from smartapi import SmartConnect    #Use SmartApi instead of smartapi if you get error
from SmartWebsocketv2 import SmartWebSocketV2
import datetime
import time
import requests
from datetime import timedelta
from pytz import timezone
import pandas as pd
import pyotp
import traceback

######PIVOT POINTS##########################
####################__INPUT__#####################

trading_api_key= 'ZD7Xc9PP'
hist_api_key = 'UIF9dBQg'
username = 'ANPDA6862'
password = '1848'   #This is 4 digit MPIN
otp_token = '2F7MF7IFKXOE72HFZJJGGKLGB4'
allinst = pd.read_json('https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json')

def login_trading():
    global trading_obj
    totp=pyotp.TOTP(otp_token).now()

    trading_obj=SmartConnect(api_key=trading_api_key)
    trading_session=trading_obj.generateSession(username,password,totp)
    print(trading_session)

    if trading_session['message'] == 'SUCCESS':
        trading_refreshToken= trading_session['data']['refreshToken']  #till here
        #trading_authToken = trading_session['data']['jwtToken']
        #trading_feedToken=trading_obj.getfeedToken()
        #print(".........................................")
        #print(trading_feedToken)
        #print("Connection Successful")
    else:
        print(trading_session['message'])

    #SmartWebSocketV2OBJ = SmartWebSocketV2(trading_authToken, trading_api_key, username, trading_feedToken)

def login_historical():
    global hist_obj
    totp=pyotp.TOTP(otp_token).now()
    hist_obj=SmartConnect(api_key=hist_api_key)
    hist_session=hist_obj.generateSession(username,password,totp)
    print(hist_session)

    if hist_session['message'] == 'SUCCESS':
        hist_refreshToken= hist_session['data']['refreshToken']
        #hist_authToken = hist_session['data']['jwtToken']
        #hist_feedToken=hist_obj.getfeedToken()
        #print(".........................................")
        #print(hist_feedToken)
        #print("Connection Successful")
    else:
        print(hist_session['message'])



def get_tokens(symbols):
    for i in range(len(allinst)):
        if symbols[4:] == "NIFTY":
            return 99926000
        elif symbols[4:] == "BANKNIFTY":
            return 99926009
        elif allinst['symbol'][i] == symbols[4:] and allinst['exch_seg'][i] == symbols[:3]:
            if allinst['expiry'][i] == "":
                exch = get_exch_type(symbols, 'NO')
            else:
                exch = get_exch_type(symbols, 'YES')
            # print(exch)
            # symbol_token=allinst['token'][i]
            print(allinst['token'][i])
            return allinst['token'][i]


def get_exch_type(symbol, exp):
    if exp == 'NO':
        if symbol[:3] == 'NSE': return 1
        elif symbol[:3] == 'BSE': return 3
    if exp == 'YES':
        if symbol[:3] == 'NFO': return 2
        elif symbol[:3] == 'BSE': return 4
        elif symbol[:3] == 'MCX': return 5
        elif symbol[:3] == 'NCDEX': return 6
        elif symbol[:3] == 'CDS': return 7



def getNiftyExpiryDate():
    nifty_expiry = {
        datetime.datetime(2023, 11, 16).date(): "16NOV23",
        datetime.datetime(2023, 11, 23).date(): "23NOV23",
        datetime.datetime(2023, 11, 30).date(): "30NOV23",
        datetime.datetime(2023, 12, 7).date(): "07DEC23",
        datetime.datetime(2023, 12, 14).date(): "14DEC23",
        datetime.datetime(2023, 12, 21).date(): "21DEC23",
        datetime.datetime(2023, 12, 28).date(): "28DEC23",
        datetime.datetime(2024, 1, 4).date(): "04JAN24",
        datetime.datetime(2024, 1, 11).date(): "11JAN24",
        datetime.datetime(2024, 1, 18).date(): "18JAN24",
        datetime.datetime(2024, 1, 25).date(): "25JAN24",
        datetime.datetime(2024, 2, 1).date(): "01FEB24",
        datetime.datetime(2024, 2, 8).date(): "08FEB24",
        datetime.datetime(2024, 2, 15).date(): "15FEB24",
        datetime.datetime(2024, 2, 22).date(): "22FEB24",
        datetime.datetime(2024, 2, 29).date(): "29FEB24",
        datetime.datetime(2024, 3, 7).date(): "07MAR24",
        datetime.datetime(2024, 3, 14).date(): "14MAR24",
        datetime.datetime(2024, 3, 21).date(): "21MAR24",
        datetime.datetime(2024, 3, 28).date(): "28MAR24",
        datetime.datetime(2024, 4, 4).date(): "04APR24",
        datetime.datetime(2024, 4, 10).date(): "10APR24",
        datetime.datetime(2024, 4, 18).date(): "18APR24",
        datetime.datetime(2024, 4, 25).date(): "25APR24",
        datetime.datetime(2024, 5, 2).date(): "02MAY24",
        datetime.datetime(2024, 5, 9).date(): "09MAY24",
        datetime.datetime(2024, 5, 16).date(): "16MAY24",
        datetime.datetime(2024, 5, 23).date(): "23MAY24",
        datetime.datetime(2024, 5, 30).date(): "30MAY24",
        datetime.datetime(2024, 6, 6).date(): "06JUN24",
        datetime.datetime(2024, 6, 13).date(): "13JUN24",
        datetime.datetime(2024, 6, 20).date(): "20JUN24",
        datetime.datetime(2024, 6, 27).date(): "27JUN24",
    }

    today = datetime.datetime.now().date()

    for date_key, value in nifty_expiry.items():
        if today <= date_key:
            print(value)
            return value

def getBankNiftyExpiryDate():
    banknifty_expiry = {
        datetime.datetime(2023, 11, 15).date(): "15NOV23",
        datetime.datetime(2023, 11, 22).date(): "22NOV23",
        datetime.datetime(2023, 11, 30).date(): "30NOV23",
        datetime.datetime(2023, 12, 6).date(): "06DEC23",
        datetime.datetime(2023, 12, 13).date(): "13DEC23",
        datetime.datetime(2023, 12, 20).date(): "20DEC23",
        datetime.datetime(2023, 12, 28).date(): "08DEC23",
        datetime.datetime(2024, 1, 3).date(): "03JAN24",
        datetime.datetime(2024, 1, 10).date(): "10JAN24",
        datetime.datetime(2024, 1, 17).date(): "17JAN24",
        datetime.datetime(2024, 1, 25).date(): "25JAN24",
        datetime.datetime(2024, 1, 31).date(): "31JAN24",
        datetime.datetime(2024, 2, 7).date(): "07FEB24",
        datetime.datetime(2024, 2, 14).date(): "14FEB24",
        datetime.datetime(2024, 2, 21).date(): "21FEB24",
        datetime.datetime(2024, 2, 29).date(): "29FEB24",
        datetime.datetime(2024, 3, 6).date(): "06MAR24",
        datetime.datetime(2024, 3, 13).date(): "13MAR24",
        datetime.datetime(2024, 3, 20).date(): "20MAR24",
        datetime.datetime(2024, 3, 27).date(): "27MAR24",
        datetime.datetime(2024, 4, 3).date(): "03APR24",
        datetime.datetime(2024, 4, 10).date(): "10APR24",
        datetime.datetime(2024, 4, 16).date(): "16APR24",
        datetime.datetime(2024, 4, 24).date(): "24APR24",
        datetime.datetime(2024, 4, 30).date(): "30APR24",
        datetime.datetime(2024, 5, 8).date(): "08MAY24",
        datetime.datetime(2024, 5, 15).date(): "15MAY24",
        datetime.datetime(2024, 5, 22).date(): "22MAY24",
        datetime.datetime(2024, 5, 29).date(): "29MAY24",
        datetime.datetime(2024, 6, 5).date(): "05JUN24",
        datetime.datetime(2024, 6, 12).date(): "12JUN24",
        datetime.datetime(2024, 6, 19).date(): "19JUN24",
        datetime.datetime(2024, 6, 26).date(): "26JUN24",
    }

    today = datetime.datetime.now().date()

    for date_key, value in banknifty_expiry.items():
        if today <= date_key:
            print(value)
            return value

def getFinNiftyExpiryDate():
    finnifty_expiry = {
        datetime.datetime(2024, 2, 20).date(): "20FEB24",
        datetime.datetime(2024, 2, 27).date(): "27FEB24",
        datetime.datetime(2024, 3, 5).date(): "05MAR24",
        datetime.datetime(2024, 3, 12).date(): "12MAR24",
        datetime.datetime(2024, 3, 19).date(): "19MAR24",
        datetime.datetime(2024, 3, 26).date(): "26MAR24",
        datetime.datetime(2024, 4, 2).date(): "02APR24",
        datetime.datetime(2024, 4, 9).date(): "09APR24",
        datetime.datetime(2024, 4, 16).date(): "16APR24",
        datetime.datetime(2024, 4, 23).date(): "23APR24",
        datetime.datetime(2024, 4, 30).date(): "30APR24",
        datetime.datetime(2024, 5, 7).date(): "07MAY24",
        datetime.datetime(2024, 5, 14).date(): "14MAY24",
        datetime.datetime(2024, 5, 21).date(): "21MAY24",
        datetime.datetime(2024, 5, 28).date(): "28MAY24",
        datetime.datetime(2024, 6, 4).date(): "04JUN24",
        datetime.datetime(2024, 6, 11).date(): "11JUN24",
        datetime.datetime(2024, 6, 18).date(): "18JUN24",
        datetime.datetime(2024, 6, 25).date(): "25JUN24",
    }

    today = datetime.datetime.now().date()

    for date_key, value in finnifty_expiry.items():
        if today <= date_key:
            print(value)
            return value

def getIndexSpot(stock):
    if stock == "BANKNIFTY":
        name = "NSE:BANKNIFTY"
    elif stock == "NIFTY":
        name = "NSE:NIFTY"
    elif stock == "FINNIFTY":
        name = "NSE:FINNIFTY"

    return name

def getOptionFormat(stock, intExpiry, strike, ce_pe):
    return "NFO:" + str(stock) + str(intExpiry)+str(strike)+str(ce_pe)

def getLTP(instrument):
    url = "http://localhost:4000/ltp?instrument=" + instrument
    try:
        resp = requests.get(url)
    except Exception as e:
        print(e)
    data = resp.json()
    return data

def manualLTP(symbol):
    global hist_obj
    exch = symbol[:3]
    sym = symbol[4:]
    tok = get_tokens(symbol)
    ltp = hist_obj.ltpData(exch, symbol, tok)
    time.sleep(1)
    return (ltp['data']['ltp'])

def placeOrder(inst ,t_type,qty,order_type,price,variety, papertrading=0):
    global trading_obj
    variety = 'NORMAL'
    exch = inst[:3]
    symbol_name = inst[4:]
    #papertrading = 0 #if this is 1, then real trades will be placed
    token = get_tokens(inst)

    try:
        if (papertrading == 1):
            Targetorderparams = {
                "variety": "NORMAL",
                "tradingsymbol": symbol_name,
                "symboltoken": token,
                "transactiontype": t_type,
                "exchange": exch,
                "ordertype": order_type,
                "producttype": "INTRADAY",
                "duration": "DAY",
                "price": price,
                "squareoff": 0,
                "stoploss": 0,
                "triggerprice": 0,
                "trailingStopLoss": 0,
                "quantity": qty
            }

            print(Targetorderparams)
            orderId = trading_obj.placeOrder(Targetorderparams)
            print("The order id is: {}".format(orderId))
            return orderId
        else:
            return 0
    except Exception as e:
        traceback.print_exc()
        print("Order placement failed: {}".format(e.message))

def getHistorical(ticker,interval,duration):
    exch = ticker[:3]
    sym = ticker[4:]
    tok = get_tokens(ticker)

    time_intervals = {
        1: "ONE_MINUTE",
        3: "THREE_MINUTE",
        5: "FIVE_MINUTE",
        10: "TEN_MINUTE",
        15: "FIFTEEN_MINUTE",
        30: "THIRTY_MINUTE",
        60: "ONE_HOUR"
    }

    interval_str = time_intervals.get(interval, "Key not found")
    interval_str = "ONE_MINUTE"

    #find todate
    current_time = datetime.datetime.now()
    previous_minute_time = current_time - timedelta(minutes=1)
    start_date = previous_minute_time - timedelta(days=duration)
    to_date_string = previous_minute_time.strftime("%Y-%m-%d %H:%M")
    start_date_string = start_date.strftime("%Y-%m-%d %H:%M")

    historyparams = {
        "exchange": str(exch),
        #  "tradingsymbol":str(sym),
        "symboltoken": str(tok),
        "interval": interval_str,
        "fromdate": start_date_string,
        "todate": to_date_string
    }
    hist_data = hist_obj.getCandleData(historicDataParams= historyparams)
    hist_data = pd.DataFrame(hist_data['data'])
    hist_data.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    hist_data['datetime2'] = hist_data['timestamp'].copy()
    hist_data['timestamp'] = pd.to_datetime(hist_data['timestamp'])
    hist_data.set_index('timestamp', inplace=True)
    finaltimeframe = str(interval)  + "min"

    # Resample to a specific time frame, for example, 30 minutes
    resampled_df = hist_data.resample(finaltimeframe).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum',
        'datetime2': 'first'
    })

    # If you want to fill any missing values with a specific method, you can use fillna
    #resampled_df = resampled_df.fillna(method='ffill')  # Forward fill

    resampled_df = resampled_df.dropna(subset=['open'])
    return (resampled_df)

def getHistorical_old(ticker,interval,duration):
    exch = ticker[:3]
    sym = ticker[4:]
    tok = get_tokens(ticker)

    time_intervals = {
        1: "ONE_MINUTE",
        3: "THREE_MINUTE",
        5: "FIVE_MINUTE",
        10: "TEN_MINUTE",
        15: "FIFTEEN_MINUTE",
        30: "THIRTY_MINUTE",
        60: "ONE_HOUR"
    }

    interval_str = time_intervals.get(interval, "Key not found")

    #find todate
    current_time = datetime.datetime.now()
    previous_minute_time = current_time - timedelta(minutes=1)
    start_date = previous_minute_time - timedelta(days=duration)
    to_date_string = previous_minute_time.strftime("%Y-%m-%d %H:%M")
    start_date_string = start_date.strftime("%Y-%m-%d %H:%M")

    historyparams = {
        "exchange": str(exch),
        #  "tradingsymbol":str(sym),
        "symboltoken": str(tok),
        "interval": interval_str,
        "fromdate": start_date_string,
        "todate": to_date_string
    }
    hist_data = hist_obj.getCandleData(historicDataParams= historyparams)
    hist_data = pd.DataFrame(hist_data['data'])
    hist_data.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    return (hist_data)