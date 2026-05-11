import yfinance as yf
import requests
import os
from watchlist import stocks, stock_names, purchases
from sentiment import analyze_sentiment

tickers = {}

def init_tickers():
    for stock in stocks:
        tickers[stock] = yf.Ticker(stock)

def add_ticker(stock):
    tickers[stock] = yf.Ticker(stock)

def remove_ticker(stock):
    tickers.pop(stock, None)

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
            "stock": stock_names[stock],
            "change": change,
            "direction": direction,
            "alert": abs(change) >= 2
        }
    
    except Exception as e:
        return {'alert': False, 'error': str(e)}
    
def get_news(stock_name: str) -> list:
    try:
        url = f"https://newsapi.org/v2/everything?q={stock_name}&apiKey={os.getenv('NEWS_API_KEY')}&pageSize=5&language=en"
        response = requests.get(url)
        data = response.json()
        return [a['title'] for a in data.get('articles', [])]
    except Exception as e:
        return []

def get_info(stock: str) -> dict:
    try:
        ticker = tickers.get(stock) or yf.Ticker(stock)
        history = ticker.history(period='5d', interval='1d')
        curr = ticker.fast_info['last_price']
        prev = history.iloc[-2]['Close']
        day_change = ((curr - prev) / prev) * 100

        try:
            news = get_news(stock_names.get(stock, stock.split('.')[0]))
            sentiment = analyze_sentiment(news) if news else {}
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