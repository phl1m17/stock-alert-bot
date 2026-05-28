import yfinance as yf
import requests
import os
from watchlist import stocks, stock_names, stock_types, purchases, accounts
from sentiment import analyze_sentiment

tickers = {}

def init_tickers():
    for stock in stocks:
        tickers[stock] = yf.Ticker(stock)

def add_ticker(stock):
    tickers[stock] = yf.Ticker(stock)

def remove_ticker(stock):
    tickers.pop(stock, None)

def get_quote_type(stock: str) -> str:
    try:
        base = stock.split('.')[0]
        info = yf.Ticker(stock).info
        qt = info.get('quoteType', '')
        if qt == 'ETF':
            return 'ETF'
        return 'EQUITY'
    except:
        return 'EQUITY'

def calc(stock: str) -> dict:
    try:
        history = yf.Ticker(stock).history(period='5d', interval='1d')
        curr = yf.Ticker(stock).fast_info['last_price']
        if len(history) < 2:
            return {'alert': False, 'error': f'Not enough data for {stock}'}
        
        prev = history.iloc[-2]['Close']
        change = ((curr - prev) / prev) * 100
        direction = "down" if change < 0 else "up"

        return {
            "stock": stock_names.get(stock, stock),
            "ticker": stock,
            "change": change,
            "direction": direction,
            "current": curr,
            "alert": abs(change) >= 2
        }
    
    except Exception as e:
        return {'alert': False, 'error': str(e)}

def get_news(stock_name: str) -> list:
    """Returns list of dicts with title and url"""
    try:
        url = f"https://newsapi.org/v2/everything?q={stock_name}&apiKey={os.getenv('NEWS_API_KEY')}&pageSize=5&language=en&sortBy=publishedAt"
        response = requests.get(url)
        data = response.json()
        return [
            {'title': a['title'], 'url': a['url']}
            for a in data.get('articles', [])
            if a.get('title') and a.get('url')
        ]
    except:
        return []

def get_current_price(stock: str) -> float:
    ticker = tickers.get(stock) or yf.Ticker(stock)
    return ticker.fast_info['last_price']

def get_info(stock: str) -> dict:
    try:
        ticker = tickers.get(stock) or yf.Ticker(stock)
        history = ticker.history(period='5d', interval='1d')
        curr = ticker.fast_info['last_price']
        prev = history.iloc[-2]['Close']
        day_change = ((curr - prev) / prev) * 100

        try:
            news = get_news(stock_names.get(stock, stock.split('.')[0]))
            headlines = [n['title'] for n in news]
            sentiment = analyze_sentiment(headlines) if headlines else {}
            sentiment_text = ", ".join(f"{v} {k}" for k, v in sentiment.items() if v > 0) if sentiment else "unavailable"
        except:
            sentiment_text = "unavailable"

        result = {
            'name': stock_names.get(stock, stock),
            'current': curr,
            'day_change': day_change,
            'sentiment': sentiment_text,
        }

        if stock in purchases:
            buy_price = purchases[stock]['price']
            shares = purchases[stock]['shares']
            gain = (curr - buy_price) * shares
            gain_pct = ((curr - buy_price) / buy_price) * 100
            result['buy_price'] = buy_price
            result['shares'] = shares
            result['gain'] = gain
            result['gain_pct'] = gain_pct

        return result
    except Exception as e:
        return {'error': str(e)}

def get_portfolio_summary(account_name: str = None) -> dict:
    summary = {}
    total_spent = 0
    total_current = 0

    target_accounts = {account_name: accounts[account_name]} if account_name and account_name in accounts else accounts

    for acct, holdings in target_accounts.items():
        summary[acct] = {}
        acct_spent = 0
        acct_current = 0

        for ticker, data in holdings.items():
            try:
                curr = get_current_price(ticker)
                buy_price = data['price']
                shares = data['shares']
                spent = buy_price * shares
                current_val = curr * shares
                gain = current_val - spent
                gain_pct = (gain / spent) * 100 if spent > 0 else 0

                summary[acct][ticker] = {
                    'name': stock_names.get(ticker, ticker),
                    'shares': shares,
                    'buy_price': buy_price,
                    'current': curr,
                    'spent': spent,
                    'current_val': current_val,
                    'gain': gain,
                    'gain_pct': gain_pct
                }

                acct_spent += spent
                acct_current += current_val
            except Exception as e:
                summary[acct][ticker] = {'error': str(e)}

        summary[acct]['_totals'] = {
            'spent': acct_spent,
            'current': acct_current,
            'gain': acct_current - acct_spent,
            'gain_pct': ((acct_current - acct_spent) / acct_spent * 100) if acct_spent > 0 else 0
        }

        total_spent += acct_spent
        total_current += acct_current

    summary['_totals'] = {
        'spent': total_spent,
        'current': total_current,
        'gain': total_current - total_spent,
        'gain_pct': ((total_current - total_spent) / total_spent * 100) if total_spent > 0 else 0
    }

    return summary