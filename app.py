import pandas as pd
import cufflinks as cf
import talib
import requests
import os
from datetime import datetime as dt
from patterns import patterns
from flask import Flask, render_template, request

app = Flask(__name__)

api_url = 'https://api.coingecko.com/api/v3'

@app.route("/", methods=['GET', 'POST'])
def index():
    pattern = request.args.get('pattern', None)
    coins_df = pd.read_csv('./daily/data.csv')
    coins = {}
    for _, row in coins_df.iterrows():
        update_from_now = (dt.now() - dt.strptime(row['last_updated'], '%Y-%m-%dT%H:%M:%S.%fZ')).total_seconds()
        h = update_from_now // 3600
        m = (update_from_now % 3600) // 60
        coins[row['id']] = {
            'id': row['id'],
            'symbol': row['symbol'].upper(),
            'name': row['name'],
            'image': row['image'],
            'market_cap': '$%.2fB' % float(row['market_cap'] / 1000000000),
            'market_cap_rank': row['market_cap_rank'],
            'total_volume': '$%.2fM' % float(row['total_volume'] / 1000000),
            'high_24h': '$%.8f' % float(row['high_24h']) if float(row['high_24h']) < 1 else '$%.2f' % float(row['high_24h']),
            'current_price': '$%.8f' % float(row['current_price']) if float(row['current_price']) < 1 else '$%.2f' % float(row['current_price']),
            'low_24h': '$%.8f' % float(row['low_24h']) if float(row['low_24h']) < 1 else '$%.2f' % float(row['low_24h']),
            'price_change_24h':'$%.8f' % float(row['price_change_24h']) if float(row['price_change_24h']) < 1 else '$%.2f' % float(row['price_change_24h']),
            'price_change_percentage_24h': '%.2f%%' % float(row['price_change_percentage_24h']),
            'total_supply': '%.2f' % float(row['total_supply']),
            'max_supply': '%.2f' % float(row['max_supply']),
            'circulating_supply': '%.2f' % float(row['circulating_supply']),
            'last_updated': '%dH, %dM ago' % (h, m),
            'pattern': None
        }
    if(pattern):
        for filename in os.listdir('./daily'):
            if('data' not in filename):
                coin_id = filename.split('.')[0]
                df = pd.read_csv(f'./daily/{filename}')
                is_true = getattr(talib, pattern)(df['Open'], df['High'], df['Low'], df['Close'])
                within = 6
                if(len([1 for it in list(is_true.tail(within)) if it > 0]) > 0):
                    coins[coin_id]['pattern'] = 'bullish'
                else:
                    coins[coin_id]['pattern'] = 'bearish'
    return render_template('index.html', patterns=patterns, coins=coins, current_pattern=pattern)

@app.route("/update-daily")
def update_daily():
    # get top 50 markets for their data
    res_top_50_markets = requests.get(api_url + '/coins/markets', {'vs_currency': 'usd', 'per_page': 50}).json()
    coins = []
    for coin in res_top_50_markets:
        coins.append({
            'id': coin['id'],
            'symbol': coin['symbol'].upper(),
            'name': coin['name'],
            'image': coin['image'],
            'market_cap': coin['market_cap'],
            'market_cap_rank': coin['market_cap_rank'],
            'total_volume': coin['total_volume'],
            'high_24h': coin['high_24h'],
            'current_price': coin['current_price'],
            'low_24h': coin['low_24h'],
            'price_change_24h': coin['price_change_24h'],
            'price_change_percentage_24h': coin['price_change_percentage_24h'],
            'total_supply': coin['total_supply'],
            'max_supply': coin['max_supply'],
            'circulating_supply': coin['circulating_supply'],
            'last_updated': coin['last_updated'],
        })

    # loop each coin id, and get their open, high, low, and close data
    for i, coin in enumerate(coins):
        coin_id = coin['id']
        res_candlestick = requests.get(api_url + f'/coins/{coin_id}/ohlc', {'vs_currency':'usd', 'days': '30'})
        res = {}
        if(res_candlestick.status_code == 200):
            data = res_candlestick.json()
            res['DateTime'] = [dt.fromtimestamp(d[0] / 1000) for d in data]
            res['Open'] = [d[1] for d in data]
            res['High'] = [d[2] for d in data]
            res['Low'] = [d[3] for d in data]
            res['Close'] = [d[4] for d in data]
            print('[%d/%d] -> %d datas were returned' % (i + 1, len(coins), len(res['DateTime'])))
        else:
            print(f'Failed to get {coin_id}\' candlestick')

        df = pd.DataFrame(res)
        df.to_csv(f'./daily/{coin_id}.csv', index=False)
        qf = cf.QuantFig(df, title='%s Chart' % coin['name'], legend='top', name='%s/USD' % coin['symbol'])
        qf.add_ema()
        qf.add_rsi()
        # qf.add_resistance()
        # qf.add_support()
        # qf.add_trendline()
        qf.figure().write_image(f'./static/charts/{coin_id}.png')
    coins_df = pd.DataFrame(coins)
    coins_df.to_csv('./daily/data.csv', index=False)
    
    return {'data': coins}