from notifier import send_text
from prompt_toolkit.patch_stdout import patch_stdout
from stocks import calc, get_news, get_quote_type
from sentiment import analyze_sentiment
from watchlist import stocks, stock_names, stock_types
from datetime import datetime, date
import time
import pytz

# Tracks URLs already sent today to avoid repeats
sent_urls: set = set()
last_reset_date: date = None

def reset_sent_urls_if_new_day():
    global sent_urls, last_reset_date
    today = date.today()
    if last_reset_date != today:
        sent_urls = set()
        last_reset_date = today

def is_market_open():
    tz = pytz.timezone("US/Eastern")
    now = datetime.now(tz)
    if now.weekday() >= 5:
        return False
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    return market_open <= now <= market_close

def get_equity_stocks() -> list:
    """Returns only EQUITY type stocks (not ETFs)"""
    return [s for s in stocks if stock_types.get(s, 'EQUITY') == 'EQUITY']

def build_alert_message(label: str) -> str:
    reset_sent_urls_if_new_day()
    equity_stocks = get_equity_stocks()
    lines = [f"📊 {label} — {datetime.now().strftime('%b %d, %I:%M %p')}"]

    # News + sentiment for equity stocks only
    news_section = []
    for stock in equity_stocks:
        name = stock_names.get(stock, stock)
        articles = get_news(name)
        new_articles = [a for a in articles if a['url'] not in sent_urls]

        if not new_articles:
            continue

        headlines = [a['title'] for a in new_articles]
        sentiment = analyze_sentiment(headlines) if headlines else {}
        sentiment_text = ", ".join(f"{v} {k}" for k, v in sentiment.items() if v > 0) or "neutral"

        block = [f"\n{name}: {sentiment_text}"]
        for a in new_articles[:3]:
            block.append(f"• {a['title']}\n  {a['url']}")
            sent_urls.add(a['url'])

        news_section.append("\n".join(block))

    if news_section:
        lines.append("\n📰 News")
        lines.extend(news_section)

    # Price movers — all stocks including ETFs
    movers = []
    for stock in stocks:
        result = calc(stock)
        if 'error' in result:
            continue
        if abs(result['change']) >= 2:
            emoji = "🚨" if abs(result['change']) >= 2 else ""
            movers.append(f"{emoji} {stock_names.get(stock, stock)}: {result['change']:+.2f}%")

    if movers:
        lines.append("\n📈 Movers (2%+)")
        lines.extend(movers)

    return "\n".join(lines)

def sleep_until(target_hour: int, target_minute: int):
    """Sleep until the next occurrence of target_hour:target_minute EST"""
    tz = pytz.timezone("US/Eastern")
    now = datetime.now(tz)
    target = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
    if now >= target:
        # already past today, sleep until tomorrow
        target = target.replace(day=target.day + 1)
    delta = (target - now).total_seconds()
    time.sleep(max(0, delta))

def monitor_loop():
    ALERT_TIMES = [
        (9, 30, "Morning Brief"),
        (12, 0, "Midday Update"),
        (15, 55, "End of Day Summary"),
    ]

    while True:
        tz = pytz.timezone("US/Eastern")
        now = datetime.now(tz)

        # Find next alert time
        next_alert = None
        for hour, minute, label in ALERT_TIMES:
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if now < target:
                next_alert = (hour, minute, label)
                break

        if next_alert is None:
            # All alerts done for today, sleep until 9:30 tomorrow
            next_alert = (9, 30, "Morning Brief")

        hour, minute, label = next_alert

        with patch_stdout():
            print(f"[monitor] Next alert: {label} at {hour:02d}:{minute:02d} EST")

        sleep_until(hour, minute)

        # Only send if market is open (or just opened/closing)
        if is_market_open() or (hour == 15 and minute == 55):
            message = build_alert_message(label)
            with patch_stdout():
                print(message)
            send_text(message)