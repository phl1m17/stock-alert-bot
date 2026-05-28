import threading
import json

lock = threading.Lock()
stocks = []
stock_names = {}
stock_types = {}
purchases = {}
accounts = {}

def save_watchlist():
    with open('watchlist.json', 'w') as f:
        json.dump({
            'stocks': stocks,
            'stock_names': stock_names,
            'stock_types': stock_types,
            'purchases': purchases,
            'accounts': accounts
        }, f, indent=2)

def load_watchlist():
    try:
        with open('watchlist.json', 'r') as f:
            data = json.load(f)
            stocks.extend(data.get('stocks', []))
            stock_names.update(data.get('stock_names', {}))
            stock_types.update(data.get('stock_types', {}))
            purchases.update(data.get('purchases', {}))
            accounts.update(data.get('accounts', {}))
    except FileNotFoundError:
        pass