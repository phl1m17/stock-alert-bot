from watchlist import load_watchlist, stocks
from stocks import init_tickers
from monitor import monitor_loop
from cli import cli_loop
from dotenv import load_dotenv
import threading
import os

if __name__ == "__main__":
    load_dotenv()
    load_watchlist()
    init_tickers()
    
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()
    os.system('clear')
    cli_loop()
