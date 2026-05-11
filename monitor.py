from notifier import send_text
from prompt_toolkit.patch_stdout import patch_stdout
from stocks import calc, get_news, stock_names
from sentiment import analyze_sentiment
from watchlist import stocks
from datetime import datetime
import time
import pytz

def job() -> tuple:
    alerts = {'Stocks':[],'News':{}}
    alerted_stocks = {}
    for stock in stocks:
        result = calc(stock)

        if result['alert']:
            alerts['Stocks'].append(result['stock'])

            news = get_news(result['stock'])
            sentiment = analyze_sentiment(news)

            alerts['News'][result['stock']] = {
                'headlines': news,
                'sentiment': sentiment
            }

            alerted_stocks[stock] = result
    
    return (alerts, alerted_stocks)

def sleep_until_next(interval=5):
    now = datetime.now()
    minutes_until_next = interval - (now.minute % interval)
    seconds = minutes_until_next * 60 - now.second
    time.sleep(seconds)

def is_market_open():
    tz = pytz.timezone("US/Eastern")
    now = datetime.now(tz)

    if now.weekday() >= 5:
        return False

    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)

    return market_open <= now <= market_close

def monitor_loop():
    while True:
        if is_market_open():
            alerts, alerted_stocks = job()
            messages = []
            for stock, data in alerted_stocks.items():
                sentiment = alerts['News'][data['stock']]['sentiment']
                sentiment_text = ", ".join(f"{v} {k}" for k, v in sentiment.items() if v > 0)
                messages.append(
                    f"{stock_names[stock]} is {data['direction']} "
                    f"{data['change']:+.2f}%. "
                    f"Sentiment: {sentiment_text}."
                )

            full_message = f"[{datetime.now().strftime('%H:%M:%S')}]\n" + "\n".join(messages)
            with patch_stdout():
                print(full_message)
            send_text(full_message)
        sleep_until_next()
