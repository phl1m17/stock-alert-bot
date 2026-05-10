import threading
import json

lock = threading.Lock()
stocks = []
stock_names = {}
purchases = {}

def save_watchlist():
    with open('watchlist.json', 'w') as f:
        json.dump({
            'stocks': stocks,
            'stock_names': stock_names,
            'purchases': purchases
        }, f)

def load_watchlist():
    try:
        with open('watchlist.json', 'r') as f:
            data = json.load(f)
            stocks.extend(data.get('stocks', []))
            stock_names.update(data.get('stock_names', {}))
            purchases.update(data.get('purchases', {}))
    except FileNotFoundError:
        pass
