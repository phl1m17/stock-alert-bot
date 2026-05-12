from prompt_toolkit import PromptSession, print_formatted_text, HTML
from prompt_toolkit.completion import Completer, Completion
from watchlist import stocks, stock_names, lock, save_watchlist, purchases
from stocks import add_ticker, remove_ticker, get_info
from monitor import is_market_open
import yfinance as yf
from prompt_toolkit.formatted_text import HTML
import html
import os

POPULAR_TICKERS = [
    # US Tech
    'AAPL', 'NVDA', 'AMD', 'INTC', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NFLX',
    'ORCL', 'CRM', 'ADBE', 'QCOM', 'TXN', 'MU', 'AMAT', 'ASML', 'ARM', 'SMCI',
    # Finance
    'JPM', 'BAC', 'GS', 'MS', 'V', 'MA', 'PYPL',
    # Other
    'BRK.B', 'JNJ', 'UNH', 'XOM', 'CVX', 'WMT', 'COST', 'NKE', 'DIS', 'BA',
    # ETFs
    'SPY', 'QQQ', 'VOO', 'VTI', 'ARKK',
    # Canadian ETFs
    'XEQT.TO', 'VFV.TO', 'ZQQ.TO', 'XIU.TO', 'XIC.TO', 'VGRO.TO', 'XGRO.TO'
]

class StockCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor.split(' ')
        
        if not text:
            return
            
        if len(text) == 1:
            commands = ['add', 'remove', 'list', 'help', 'buy', 'info', 'exit', 'clear', 'sell']
            for cmd in commands:
                if cmd.startswith(text[0].lower()):
                    yield Completion(cmd, start_position=-len(text[0]))

        elif text[0].lower() == 'list':
            word = text[-1].lower()
            if len(text) == 1 or not text[-1]:
                return
            if 'all'.startswith(word):
                yield Completion('all', start_position=-len(text[-1]))

        elif text[0].lower() == 'add' or text[0].lower() == 'buy':
            word = text[-1].upper()
            if len(text) == 1 or not text[-1]:
                return
            for ticker in set(POPULAR_TICKERS + stocks):
                if ticker.startswith(word):
                    yield Completion(ticker, start_position=-len(text[-1]))

        elif text[0].lower() == 'sell':
            word = text[-1].upper()
            if len(text) == 1 or not text[-1]:
                return
            for ticker in purchases:
                if ticker.startswith(word):
                    yield Completion(ticker, start_position=-len(text[-1]))

        elif text[0].lower() == 'remove':
            word = text[-1].upper()
            if len(text) == 1 or not text[-1]:
                return
            for ticker in stocks:
                if ticker.startswith(word):
                    yield Completion(ticker, start_position=-len(text[-1]))
        
        elif text[0].lower() == 'info':
            if len(text) < 2 or not text[-1]:
                return
            word = text[-1].upper()
            for ticker in set(POPULAR_TICKERS + stocks + ['ALL']):
                if ticker.startswith(word):
                    yield Completion(ticker, start_position=-len(text[-1]))


def is_valid_ticker(stock: str) -> bool:
    try:
        info = yf.Ticker(stock).info
        return info.get('symbol') is not None
    except:
        return False

def get_display_name(stock: str) -> str:
    try:
        base = stock.split('.')[0]
        name = yf.Ticker(base).info.get('longName') or yf.Ticker(stock).info.get('longName')
        if not name:
            return base
        return name.replace('Inc.', '').replace('Corporation', '').replace('Corp.', '').strip()
    except:
        return stock.split('.')[0]


def toolbar():
    return f'Market: {"Open" if is_market_open() else "Closed"}'

def cli_loop():
    session = PromptSession(completer=StockCompleter(), bottom_toolbar=toolbar)
    print_formatted_text(HTML('<b><green>---| Stock Alert Bot |---</green></b>'))
    print_formatted_text(HTML('<i>Type help for available commands</i>'))

    while True:
        try:
            user_input = session.prompt('>> ').strip()
            if not user_input:
                continue

            parts = user_input.split()
            action = parts[0].lower()
            args = parts[1:]

            if action == 'add':
                if not args:
                    print_formatted_text(HTML('<ansiyellow>Usage: add TICKER1 TICKER2</ansiyellow>'))
                    continue
                with lock:
                    for ticker in args:
                        ticker = ticker.upper()
                        if not is_valid_ticker(ticker):
                            print_formatted_text(HTML(f'<ansired>✗ {ticker} is not a valid ticker</ansired>'))
                            continue
                        if ticker in stocks:
                            print_formatted_text(HTML(f'<ansiyellow>⚠ {ticker} already in watchlist</ansiyellow>'))
                            continue
                        name = get_display_name(ticker)
                        stocks.append(ticker)
                        stock_names[ticker] = name
                        add_ticker(ticker)
                        save_watchlist()
                        safe_name = html.escape(name)
                        print_formatted_text(HTML(f'<ansigreen>✓ Added {safe_name} ({ticker})</ansigreen>'))

            elif action == 'remove':
                if not args:
                    print_formatted_text(HTML('<ansiyellow>Usage: remove TICKER1 TICKER2</ansiyellow>'))
                    continue
                with lock:
                    for ticker in args:
                        ticker = ticker.upper()
                        if ticker not in stocks:
                            print_formatted_text(HTML(f'<ansiyellow>⚠ {ticker} not in watchlist</ansiyellow>'))
                            continue
                        stocks.remove(ticker)
                        stock_names.pop(ticker, None)
                        remove_ticker(ticker)
                        save_watchlist()
                        print_formatted_text(HTML(f'<ansired>✗ Removed {ticker}</ansired>'))

            elif action == 'list':
                if args and args[0].lower() == 'all':
                    with lock:
                        if not purchases:
                            print_formatted_text(HTML('<ansiyellow>No purchases logged</ansiyellow>'))
                        else:
                            print_formatted_text(HTML('<b><ansiwhite>── Purchases ──</ansiwhite></b>'))
                            for ticker, data in purchases.items():
                                safe_name = html.escape(stock_names.get(ticker, ticker))
                                print_formatted_text(HTML(
                                    f'<ansicyan>  {safe_name} ({ticker})</ansicyan>'
                                    f'<ansiwhite> — ${data["price"]:.2f} × {data["shares"]} shares</ansiwhite>'
                                ))
                else:
                    with lock:
                        if not stocks:
                            print_formatted_text(HTML('<ansiyellow>Watchlist is empty</ansiyellow>'))
                        else:
                            print_formatted_text(HTML('<b><ansiwhite>── Watchlist ──</ansiwhite></b>'))
                            for ticker in stocks:
                                print_formatted_text(HTML(
                                    f'<ansicyan>  {html.escape(stock_names.get(ticker, ticker))} ({ticker})</ansicyan>'
                                ))

            elif action == 'info':
                if not args:
                    print_formatted_text(HTML('<ansiyellow>Usage: info TICKER | info all</ansiyellow>'))
                    continue
                with lock:
                    tickers_to_check = stocks if args[0].lower() == 'all' else [args[0].upper()]
                    for ticker in tickers_to_check:
                        info = get_info(ticker)
                        if 'error' in info:
                            print_formatted_text(HTML(f'<ansired>✗ {ticker}: {html.escape(info["error"])}</ansired>'))
                            continue
                        day_color = 'ansigreen' if info['day_change'] >= 0 else 'ansired'
                        print_formatted_text(HTML(
                            f'<b><ansiwhite>{html.escape(info["name"])} ({ticker})</ansiwhite></b>\n'
                            f'<ansiwhite>  Current:    ${info["current"]:.2f}</ansiwhite>\n'
                            f'<{day_color}>  Day change: {info["day_change"]:+.2f}%</{day_color}>'
                        ))
                        if 'buy_price' in info:
                            gain_color = 'ansigreen' if info['gain'] >= 0 else 'ansired'
                            print_formatted_text(HTML(
                                f'<ansiwhite>  Bought at:  ${info["buy_price"]:.2f} × {info["shares"]} shares</ansiwhite>\n'
                                f'<{gain_color}>  Gain/Loss:  ${info["gain"]:+.2f} ({info["gain_pct"]:+.1f}%)</{gain_color}>'
                            ))
                        print_formatted_text(HTML(
                            f'<ansiwhite>  Sentiment:  {info["sentiment"]}</ansiwhite>'
                        ))
                        if len(tickers_to_check) > 1:
                            print_formatted_text(HTML('<ansiwhite>  ──────────────────────</ansiwhite>'))

            elif action == 'buy':
                if len(args) < 3:
                    print_formatted_text(HTML('<ansiyellow>Usage: buy TICKER PRICE SHARES</ansiyellow>'))
                    continue
                with lock:
                    ticker = args[0].upper()
                    try:
                        price = float(args[1])
                        shares = float(args[2])
                    except ValueError:
                        print_formatted_text(HTML('<ansired>✗ Price and shares must be numbers</ansired>'))
                        continue
                    if not is_valid_ticker(ticker):
                        print_formatted_text(HTML(f'<ansired>✗ {ticker} is not a valid ticker</ansired>'))
                        continue
                    if ticker not in stocks:
                        name = get_display_name(ticker)
                        stocks.append(ticker)
                        stock_names[ticker] = name
                        add_ticker(ticker)
                    safe_name = html.escape(stock_names.get(ticker, ticker))
                    if ticker in purchases:
                        old_price = purchases[ticker]['price']
                        old_shares = purchases[ticker]['shares']
                        avg_price = ((old_price * old_shares) + (price * shares)) / (old_shares + shares)
                        purchases[ticker]['price'] = avg_price
                        purchases[ticker]['shares'] = old_shares + shares
                        safe_name = html.escape(stock_names.get(ticker, ticker))
                        print_formatted_text(HTML(
                            f'<ansigreen>✓ Updated {safe_name} ({ticker}) — '
                            f'avg ${avg_price:.2f} × {purchases[ticker]["shares"]} shares</ansigreen>'
                        ))
                    else:
                        purchases[ticker] = {'price': price, 'shares': shares}
                        print_formatted_text(HTML(
                            f'<ansigreen>✓ Logged {safe_name} ({ticker}) at ${price:.2f} × {shares} shares</ansigreen>'
                        ))
                    save_watchlist()

            elif action == 'sell':
                if len(args) < 2:
                    print_formatted_text(HTML('<ansiyellow>Usage: sell TICKER SHARES | sell TICKER all</ansiyellow>'))
                    continue
                with lock:
                    ticker = args[0].upper()
                    if ticker not in purchases:
                        print_formatted_text(HTML(f'<ansired>✗ No purchase logged for {ticker}</ansired>'))
                        continue
                    if args[1].lower() == 'all':
                        del purchases[ticker]
                        save_watchlist()
                        print_formatted_text(HTML(f'<ansiyellow>✗ Removed all shares for {ticker}</ansiyellow>'))
                    else:
                        try:
                            shares = float(args[1])
                            purchases[ticker]['shares'] -= shares
                            if purchases[ticker]['shares'] <= 0:
                                del purchases[ticker]
                                save_watchlist()
                                print_formatted_text(HTML(f'<ansiyellow>✗ Removed all shares for {ticker}</ansiyellow>'))
                            else:
                                save_watchlist()
                                safe_name = html.escape(stock_names.get(ticker, ticker))
                                print_formatted_text(HTML(
                                    f'<ansigreen>✓ Updated {safe_name} ({ticker}) — '
                                    f'{purchases[ticker]["shares"]} shares remaining</ansigreen>'
                                ))
                        except ValueError:
                            print_formatted_text(HTML('<ansired>✗ Shares must be a number or "all"</ansired>'))

            elif action == 'clear':
                os.system('clear')
                print_formatted_text(HTML('<b><ansigreen>---| Stock Alert Bot |---</ansigreen></b>'))
                print_formatted_text(HTML('<i><ansiwhite>Type help for available commands</ansiwhite></i>'))

            elif action == 'help':
                print_formatted_text(HTML(
                    '<b><ansiwhite>── Commands ──</ansiwhite></b>\n'
                    '<ansicyan>  add TICKER1 TICKER2       </ansicyan><ansiwhite>add stocks to watchlist</ansiwhite>\n'
                    '<ansicyan>  remove TICKER1 TICKER2    </ansicyan><ansiwhite>remove stocks from watchlist</ansiwhite>\n'
                    '<ansicyan>  list                      </ansicyan><ansiwhite>show watchlist</ansiwhite>\n'
                    '<ansicyan>  list all                  </ansicyan><ansiwhite>show logged purchases</ansiwhite>\n'
                    '<ansicyan>  info TICKER               </ansicyan><ansiwhite>price, day change, gain/loss</ansiwhite>\n'
                    '<ansicyan>  buy TICKER PRICE SHARES   </ansicyan><ansiwhite>log a purchase</ansiwhite>\n'
                    '<ansicyan>  sell TICKER SHARES        </ansicyan><ansiwhite>remove shares</ansiwhite>\n'
                    '<ansicyan>  sell TICKER all           </ansicyan><ansiwhite>clear all shares</ansiwhite>\n'
                    '<ansicyan>  clear                     </ansicyan><ansiwhite>clear screen</ansiwhite>\n'
                    '<ansicyan>  exit                      </ansicyan><ansiwhite>quit</ansiwhite>'
                ))

            elif action == 'exit':
                break

            else:
                print_formatted_text(HTML(f'<ansired>✗ Unknown command: {action}. Type help.</ansired>'))

        except KeyboardInterrupt:
            break