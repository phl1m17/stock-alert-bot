from prompt_toolkit import PromptSession, print_formatted_text, HTML
from prompt_toolkit.completion import Completer, Completion
from watchlist import stocks, stock_names, stock_types, lock, save_watchlist, purchases, accounts
from stocks import add_ticker, remove_ticker, get_info, get_portfolio_summary, get_quote_type
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

ACCOUNT_TYPES = ['TFSA', 'FHSA', 'RRSP', 'MARGIN', 'CASH']

class StockCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor.split(' ')
        
        if not text:
            return
            
        if len(text) == 1:
            commands = ['add', 'remove', 'list', 'help', 'buy', 'info', 'exit', 'clear', 'sell', 'account', 'portfolio']
            for cmd in commands:
                if cmd.startswith(text[0].lower()):
                    yield Completion(cmd, start_position=-len(text[0]))

        elif text[0].lower() == 'list':
            word = text[-1].lower()
            if not text[-1]:
                return
            for opt in ['all', 'purchases']:
                if opt.startswith(word):
                    yield Completion(opt, start_position=-len(text[-1]))

        elif text[0].lower() == 'account':
            if len(text) == 2:
                word = text[-1].lower()
                for opt in ['add', 'remove', 'list']:
                    if opt.startswith(word):
                        yield Completion(opt, start_position=-len(text[-1]))
            elif len(text) == 3 and text[1].lower() in ['add', 'remove']:
                word = text[-1].upper()
                for acct in ACCOUNT_TYPES:
                    if acct.startswith(word):
                        yield Completion(acct, start_position=-len(text[-1]))

        elif text[0].lower() == 'portfolio':
            if len(text) == 2:
                word = text[-1].upper()
                for acct in list(accounts.keys()) + ['all']:
                    if acct.upper().startswith(word):
                        yield Completion(acct, start_position=-len(text[-1]))

        elif text[0].lower() == 'buy':
            if len(text) == 2:
                word = text[-1].upper()
                for acct in accounts.keys():
                    if acct.startswith(word):
                        yield Completion(acct, start_position=-len(text[-1]))
            elif len(text) == 3:
                word = text[-1].upper()
                if not text[-1]:
                    return
                for ticker in set(POPULAR_TICKERS + stocks):
                    if ticker.startswith(word):
                        yield Completion(ticker, start_position=-len(text[-1]))

        elif text[0].lower() == 'add':
            word = text[-1].upper()
            if not text[-1]:
                return
            for ticker in set(POPULAR_TICKERS + stocks):
                if ticker.startswith(word):
                    yield Completion(ticker, start_position=-len(text[-1]))

        elif text[0].lower() == 'sell':
            word = text[-1].upper()
            if not text[-1]:
                return
            for ticker in purchases:
                if ticker.startswith(word):
                    yield Completion(ticker, start_position=-len(text[-1]))

        elif text[0].lower() == 'remove':
            word = text[-1].upper()
            if not text[-1]:
                return
            for ticker in stocks:
                if ticker.startswith(word):
                    yield Completion(ticker, start_position=-len(text[-1]))
        
        elif text[0].lower() == 'info':
            if not text[-1]:
                return
            word = text[-1].upper()
            for ticker in set(POPULAR_TICKERS + stocks + ['ALL']):
                if ticker.startswith(word):
                    yield Completion(ticker, start_position=-len(text[-1]))

        elif text[0].lower() == 'account':
            if len(text) == 2:
                word = text[-1].lower()
                for opt in ['add', 'remove', 'list']:
                    if opt.startswith(word):
                        yield Completion(opt, start_position=-len(text[-1]))
            elif len(text) == 3 and text[1].lower() in ['add', 'remove']:
                word = text[-1].upper()
                for acct in ACCOUNT_TYPES + list(accounts.keys()):
                    if acct.startswith(word):
                        yield Completion(acct, start_position=-len(text[-1]))

            elif text[0].lower() == 'portfolio':
                if len(text) == 2:
                    word = text[-1].upper()
                    for acct in list(accounts.keys()) + ['ALL']:
                        if acct.upper().startswith(word):
                            yield Completion(acct, start_position=-len(text[-1]))


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

def print_portfolio(summary: dict, account_name: str = None):
    for acct, holdings in summary.items():
        if acct == '_totals':
            continue
        print_formatted_text(HTML(f'<b><ansiwhite>── {html.escape(acct)} ──────────────────────</ansiwhite></b>'))
        for ticker, data in holdings.items():
            if ticker == '_totals':
                continue
            if 'error' in data:
                print_formatted_text(HTML(f'<ansired>  ✗ {ticker}: {html.escape(data["error"])}</ansired>'))
                continue
            gain_color = 'ansigreen' if data['gain'] >= 0 else 'ansired'
            safe_name = html.escape(data['name'])
            print_formatted_text(HTML(
                f'<ansicyan>  {safe_name} ({ticker})</ansicyan>\n'
                f'<ansiwhite>    {data["shares"]} shares @ ${data["buy_price"]:.2f} → ${data["current"]:.2f}</ansiwhite>  '
                f'<{gain_color}>${data["gain"]:+.2f} ({data["gain_pct"]:+.1f}%)</{gain_color}>'
            ))
        totals = holdings.get('_totals', {})
        if totals:
            gain_color = 'ansigreen' if totals['gain'] >= 0 else 'ansired'
            print_formatted_text(HTML(
                f'<ansiwhite>  Spent: ${totals["spent"]:,.2f}  |  '
                f'Current: ${totals["current"]:,.2f}  |  </ansiwhite>'
                f'<{gain_color}>Gain: ${totals["gain"]:+,.2f} ({totals["gain_pct"]:+.1f}%)</{gain_color}>'
            ))
        print_formatted_text(HTML('<ansiwhite>  ──────────────────────────────</ansiwhite>'))

    totals = summary.get('_totals', {})
    if totals and not account_name:
        gain_color = 'ansigreen' if totals['gain'] >= 0 else 'ansired'
        print_formatted_text(HTML(
            f'<b><ansiwhite>── TOTAL ───────────────────────</ansiwhite></b>\n'
            f'<ansiwhite>  Spent: ${totals["spent"]:,.2f}  |  Current: ${totals["current"]:,.2f}  |  </ansiwhite>'
            f'<{gain_color}>Gain: ${totals["gain"]:+,.2f} ({totals["gain_pct"]:+.1f}%)</{gain_color}>'
        ))

def toolbar():
    return f'Market: {"Open" if is_market_open() else "Closed"}'

def cli_loop():
    session = PromptSession(completer=StockCompleter(), bottom_toolbar=toolbar)
    print_formatted_text(HTML('<b><ansigreen>---| Stock Alert Bot |---</ansigreen></b>'))
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
                        quote_type = get_quote_type(ticker)
                        stocks.append(ticker)
                        stock_names[ticker] = name
                        stock_types[ticker] = quote_type
                        add_ticker(ticker)
                        save_watchlist()
                        safe_name = html.escape(name)
                        type_label = " (ETF)" if quote_type == "ETF" else ""
                        print_formatted_text(HTML(f'<ansigreen>✓ Added {safe_name} ({ticker}){type_label}</ansigreen>'))

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

            elif action == 'account':
                if not args:
                    print_formatted_text(HTML('<ansiyellow>Usage: account add NAME | account remove NAME | account list</ansiyellow>'))
                    continue
                sub = args[0].lower()
                if sub == 'list':
                    if not accounts:
                        print_formatted_text(HTML('<ansiyellow>No accounts created</ansiyellow>'))
                    else:
                        print_formatted_text(HTML('<b><ansiwhite>── Accounts ──</ansiwhite></b>'))
                        for acct in accounts:
                            holdings = len(accounts[acct])
                            print_formatted_text(HTML(f'<ansicyan>  {html.escape(acct)} — {holdings} holding(s)</ansicyan>'))
                elif sub == 'add':
                    if len(args) < 2:
                        print_formatted_text(HTML('<ansiyellow>Usage: account add NAME</ansiyellow>'))
                        continue
                    acct_name = args[1].upper()
                    if acct_name in accounts:
                        print_formatted_text(HTML(f'<ansiyellow>⚠ {acct_name} already exists</ansiyellow>'))
                    else:
                        accounts[acct_name] = {}
                        save_watchlist()
                        print_formatted_text(HTML(f'<ansigreen>✓ Created account {acct_name}</ansigreen>'))
                elif sub == 'remove':
                    if len(args) < 2:
                        print_formatted_text(HTML('<ansiyellow>Usage: account remove NAME</ansiyellow>'))
                        continue
                    acct_name = args[1].upper()
                    if acct_name not in accounts:
                        print_formatted_text(HTML(f'<ansired>✗ Account {acct_name} not found</ansired>'))
                    else:
                        del accounts[acct_name]
                        save_watchlist()
                        print_formatted_text(HTML(f'<ansired>✗ Removed account {acct_name}</ansired>'))
                else:
                    print_formatted_text(HTML('<ansired>✗ Unknown subcommand. Use: add, remove, list</ansired>'))

            elif action == 'list':
                if args and args[0].lower() == 'purchases':
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

            elif action == 'portfolio':
                with lock:
                    if not accounts:
                        print_formatted_text(HTML('<ansiyellow>No accounts found. Create one with: account add TFSA</ansiyellow>'))
                        continue
                    acct_filter = args[0].upper() if args and args[0].lower() != 'all' else None
                    if acct_filter and acct_filter not in accounts:
                        print_formatted_text(HTML(f'<ansired>✗ Account {acct_filter} not found</ansired>'))
                        continue
                    print_formatted_text(HTML('<ansiwhite>Fetching portfolio data...</ansiwhite>'))
                    summary = get_portfolio_summary(acct_filter)
                    print_portfolio(summary, acct_filter)

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
                        print_formatted_text(HTML(f'<ansiwhite>  Sentiment:  {info["sentiment"]}</ansiwhite>'))
                        if len(tickers_to_check) > 1:
                            print_formatted_text(HTML('<ansiwhite>  ──────────────────────</ansiwhite>'))

            elif action == 'buy':
                # Usage: buy ACCOUNT TICKER PRICE SHARES
                if len(args) < 4:
                    print_formatted_text(HTML('<ansiyellow>Usage: buy ACCOUNT TICKER PRICE SHARES</ansiyellow>'))
                    continue
                with lock:
                    acct_name = args[0].upper()
                    ticker = args[1].upper()
                    if acct_name not in accounts:
                        print_formatted_text(HTML(f'<ansired>✗ Account {acct_name} not found. Create it with: account add {acct_name}</ansired>'))
                        continue
                    try:
                        price = float(args[2])
                        shares = float(args[3])
                    except ValueError:
                        print_formatted_text(HTML('<ansired>✗ Price and shares must be numbers</ansired>'))
                        continue
                    if not is_valid_ticker(ticker):
                        print_formatted_text(HTML(f'<ansired>✗ {ticker} is not a valid ticker</ansired>'))
                        continue
                    if ticker not in stocks:
                        name = get_display_name(ticker)
                        quote_type = get_quote_type(ticker)
                        stocks.append(ticker)
                        stock_names[ticker] = name
                        stock_types[ticker] = quote_type
                        add_ticker(ticker)
                    safe_name = html.escape(stock_names.get(ticker, ticker))

                    # Update account holdings
                    if ticker in accounts[acct_name]:
                        old_price = accounts[acct_name][ticker]['price']
                        old_shares = accounts[acct_name][ticker]['shares']
                        avg_price = ((old_price * old_shares) + (price * shares)) / (old_shares + shares)
                        accounts[acct_name][ticker]['price'] = avg_price
                        accounts[acct_name][ticker]['shares'] = old_shares + shares
                        print_formatted_text(HTML(
                            f'<ansigreen>✓ Updated {safe_name} in {acct_name} — '
                            f'avg ${avg_price:.2f} × {accounts[acct_name][ticker]["shares"]} shares</ansigreen>'
                        ))
                    else:
                        accounts[acct_name][ticker] = {'price': price, 'shares': shares}
                        print_formatted_text(HTML(
                            f'<ansigreen>✓ Logged {safe_name} ({ticker}) in {acct_name} at ${price:.2f} × {shares} shares</ansigreen>'
                        ))

                    # Also update flat purchases for info command
                    if ticker in purchases:
                        old_price = purchases[ticker]['price']
                        old_shares = purchases[ticker]['shares']
                        avg_price = ((old_price * old_shares) + (price * shares)) / (old_shares + shares)
                        purchases[ticker]['price'] = avg_price
                        purchases[ticker]['shares'] = old_shares + shares
                    else:
                        purchases[ticker] = {'price': price, 'shares': shares}

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
                        for acct in accounts.values():
                            acct.pop(ticker, None)
                        save_watchlist()
                        print_formatted_text(HTML(f'<ansiyellow>✗ Removed all shares for {ticker}</ansiyellow>'))
                    else:
                        try:
                            shares = float(args[1])
                            purchases[ticker]['shares'] -= shares
                            if purchases[ticker]['shares'] <= 0:
                                del purchases[ticker]
                                for acct in accounts.values():
                                    acct.pop(ticker, None)
                                save_watchlist()
                                print_formatted_text(HTML(f'<ansiyellow>✗ Removed all shares for {ticker}</ansiyellow>'))
                            else:
                                # Update account holdings proportionally
                                for acct in accounts.values():
                                    if ticker in acct:
                                        acct[ticker]['shares'] -= shares
                                        if acct[ticker]['shares'] <= 0:
                                            del acct[ticker]
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
                    '<ansicyan>  add TICKER1 TICKER2                </ansicyan><ansiwhite>add stocks to watchlist</ansiwhite>\n'
                    '<ansicyan>  remove TICKER1 TICKER2             </ansicyan><ansiwhite>remove stocks from watchlist</ansiwhite>\n'
                    '<ansicyan>  list                               </ansicyan><ansiwhite>show watchlist</ansiwhite>\n'
                    '<ansicyan>  list purchases                     </ansicyan><ansiwhite>show all logged purchases</ansiwhite>\n'
                    '<ansicyan>  account add NAME                   </ansicyan><ansiwhite>create an account (TFSA, FHSA, RRSP...)</ansiwhite>\n'
                    '<ansicyan>  account remove NAME                </ansicyan><ansiwhite>delete an account</ansiwhite>\n'
                    '<ansicyan>  account list                       </ansicyan><ansiwhite>show all accounts</ansiwhite>\n'
                    '<ansicyan>  buy ACCOUNT TICKER PRICE SHARES    </ansicyan><ansiwhite>log a purchase to an account</ansiwhite>\n'
                    '<ansicyan>  sell TICKER SHARES                 </ansicyan><ansiwhite>remove shares</ansiwhite>\n'
                    '<ansicyan>  sell TICKER all                    </ansicyan><ansiwhite>clear all shares for a stock</ansiwhite>\n'
                    '<ansicyan>  portfolio                          </ansicyan><ansiwhite>show full portfolio summary</ansiwhite>\n'
                    '<ansicyan>  portfolio ACCOUNT                  </ansicyan><ansiwhite>show one account summary</ansiwhite>\n'
                    '<ansicyan>  info TICKER                        </ansicyan><ansiwhite>price, day change, gain/loss</ansiwhite>\n'
                    '<ansicyan>  info all                           </ansicyan><ansiwhite>info for all watchlist stocks</ansiwhite>\n'
                    '<ansicyan>  clear                              </ansicyan><ansiwhite>clear screen</ansiwhite>\n'
                    '<ansicyan>  exit                               </ansicyan><ansiwhite>quit</ansiwhite>'
                ))

            elif action == 'exit':
                break

            else:
                print_formatted_text(HTML(f'<ansired>✗ Unknown command: {action}. Type help.</ansired>'))

        except KeyboardInterrupt:
            break