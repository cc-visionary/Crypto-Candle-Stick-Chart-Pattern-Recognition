import pandas as pd
import numpy as np
import requests
import os
from datetime import datetime as dt
from patterns import patterns
from flask import Flask, render_template, request

app = Flask(__name__)

api_url = 'https://api.coingecko.com/api/v3'

@app.route("/")
def index():
    pattern = request.args.get('pattern', None)
    if(pattern):
        for filename in os.listdir('./daily'):
            df = pd.read_csv(f'./daily/{filename}')

    return render_template('index.html', patterns=patterns)

@app.route("/update-daily")
def update_daily():
    coin_ids = [
        'shiba-inu', 
        'ethereum', 
        'cardano', 
        'bitcoin', 
        'ripple', 
        'dogecoin', 
        'cosmos', 
        'chainlink', 
        'tezos', 
        'polkadot',
        'uniswap',
        'burger-swap',
        'binancecoin',
        'vechain',
        'safemoon',
        'yearn-finance'
    ]
    # get top 100 markets for their id
    res_top_100_markets = requests.get(api_url + '/coins/markets', {'vs_currency': 'usd'})
    if(res_top_100_markets.status_code == 200):
        for coin in res_top_100_markets.json():
            if(coin['id'] not in coin_ids):
                coin_ids.append(coin['id'])
    result = {}
    # loop each coin id, and get their open, high, low, and close data
    for i, coin_id in enumerate(coin_ids):
        res_candlestick = requests.get(api_url + f'/coins/{coin_id}/ohlc', {'vs_currency':'usd', 'days': '30'})
        res = {}
        data = {}
        if(res_candlestick.status_code == 200):
            data = res_candlestick.json()
            res['datetime'] = [dt.fromtimestamp(d[0] / 1000) for d in data]
            res['open'] = [d[1] for d in data]
            res['high'] = [d[2] for d in data]
            res['low'] = [d[3] for d in data]
            res['close'] = [d[4] for d in data]
            print('[%d/%d] -> %d datas were returned' % (i, len(coin_ids), len(res['datetime'])))
        else:
            print(f'Failed to get {coin_id}\' candlestick')

        result[coin_id] = res

        df = pd.DataFrame(res)
        df.to_csv(f'./daily/{coin_id}.csv', index=False)
        
    return {'data': result}