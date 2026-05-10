# stock-alert-bot

A Python-based stock monitoring agent that texts you when your holdings move significantly. Runs continuously in the background, checks your watchlist every 5 minutes during market hours, and sends SMS alerts via Twilio. Includes a full CLI for managing your watchlist and tracking purchases.

## Features

- Real-time stock price monitoring via yfinance
- SMS alerts via Twilio when stocks move 2%+ from yesterday's close
- FinBERT-powered sentiment analysis on news headlines
- News fetching via NewsAPI
- Interactive CLI with autocomplete, watchlist management, and purchase tracking
- Market hours awareness (NYSE, Mon–Fri 9:30–4:00 EST)
- Persistent watchlist and purchase history via JSON

## Tech Stack

- **yfinance** — stock price data
- **FinBERT** (ProsusAI/finbert) — financial sentiment analysis
- **NewsAPI** — news headlines
- **Twilio** — SMS delivery
- **prompt_toolkit** — interactive CLI
- **transformers + PyTorch** — FinBERT inference

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/phl1m17/stock-alert-bot.git
cd stock-alert-bot
```

### 2. Install dependencies

```bash
pip install yfinance transformers torch requests twilio python-dotenv pytz prompt_toolkit
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```
TWILIO_SID=your_twilio_account_sid
TWILIO_TOKEN=your_twilio_auth_token
TWILIO_FROM=your_twilio_phone_number
TWILIO_TO=your_personal_phone_number
NEWS_API_KEY=your_newsapi_key
```

- Twilio: sign up at [twilio.com](https://twilio.com) — free trial included
- NewsAPI: sign up at [newsapi.org](https://newsapi.org) — free tier available

### 4. Run

```bash
python3 main.py
```

The bot will load your watchlist, start the monitor thread, and open the CLI.

## CLI Commands

```
add TICKER1 TICKER2       add stocks to watchlist (space separated, no commas)
remove TICKER1 TICKER2    remove stocks from watchlist
list                      show current watchlist
list purchases            show logged purchases
info TICKER               show price, day change, sentiment, and gain/loss
info all                  show info for all stocks in watchlist
buy TICKER PRICE SHARES   log a purchase (price per share)
sell TICKER SHARES        remove shares from a logged purchase
sell TICKER all           clear all shares for a stock
clear                     clear the screen
help                      show available commands
exit                      quit
```

### Examples

```
>> add NVDA AAPL MSFT
>> buy NVDA 115.00 10
>> info NVDA
>> info all
>> list purchases
>> remove AAPL
```

### Canadian Tickers

Append `.TO` for TSX-listed ETFs and `.NE` for NEO Exchange CDRs:

```
>> add XEQT.TO VFV.TO NVDA.NE AMD.NE
```

## Project Structure

```
stock-alert-bot/
├── main.py          # entry point, threading setup
├── monitor.py       # monitoring loop, market hours, job scheduler
├── stocks.py        # price fetching, news, stock info
├── sentiment.py     # FinBERT sentiment analysis
├── notifier.py      # Twilio SMS
├── watchlist.py     # persistent watchlist and purchase storage
├── cli.py           # interactive CLI
├── watchlist.json   # auto-generated on first run
├── .env             # your credentials (not committed)
└── .gitignore
```

## Notes

- The bot runs as long as your machine is on. For true 24/7 monitoring, deploy to a VPS or Raspberry Pi.
- FinBERT model (~440MB) is downloaded on first run and cached locally.
- NewsAPI free tier allows 100 requests/day.
- Twilio free trial prepends "Sent from your Twilio trial account" to messages.

## License

MIT — see [LICENSE](LICENSE)
