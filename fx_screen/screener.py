from settings_handler import ScreeningOptionsHandler
import os
from datetime import datetime, timedelta
import requests
from utils import get_ticker_history
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt

class Screener:
    def __init__(self, screen_key, POLYGON_KEY, handler: ScreeningOptionsHandler, logger):
        self.screen_key = screen_key
        self.handler = handler
        self.logger = logger
        self.POLYGON_KEY = POLYGON_KEY
        self.SCREEN_PATH = f'data/screen_results/{self.screen_key}'
        self.count = 0
        if os.path.exists(self.SCREEN_PATH) is False:
            os.makedirs(self.SCREEN_PATH)
    
    def screen(self):
        options = self.handler.get_options()
        self.logger.info(f"Screening starts with key {self.screen_key}")
        self.logger.info(f"Screening options: {list(options.keys())}")
        for option_name, details in options.items():
            active = details.get('active', False)
            if active:
                self.screen_option(option_name, details)
            
    
    def screen_option(self, option_name, details):
        self.logger.info(f"Processing option {option_name}")
        option_path = f'{self.SCREEN_PATH}/{option_name}'
        if os.path.exists(option_path) is False:
            os.makedirs(option_path)
        
        observed_tickers = details.get('observed_tickers', [])
        depth = 50
        today = datetime.now()
        for ticker in observed_tickers:
            if self.count % 4 == 0:
                self.logger.info("Sleeping for 1 minute to avoid rate limit")
            
            start_date = today - timedelta(days=depth)
            ticker_c = f"C:{ticker}"
            response = requests.get(get_ticker_history(ticker_c, start_date, today, self.POLYGON_KEY))
            if response.status_code == 200:
                response = response.json()
                data = response.get("results", None)
                if data is None:
                    self.logger.error(f"Error in fetching data for {ticker}")
                    continue
                historical_data = self.clean_data(data)
                mpf.plot(historical_data, type='candle', style='charles', title=f"{ticker} {depth}")
                plt.savefig(os.path.join(option_path, f'history_{ticker_c}.png'), format='png')
                plt.close()
                
                self.logger.info(f"Data fetched for {ticker}")
            else:
                self.logger.error(f"Error in fetching data for {ticker}")
            self.count += 1


    def clean_data(self, data):
        historical_data = pd.DataFrame(data)
        self.logger.info(f"Data head: {historical_data.head()}")
        historical_data['date'] = pd.to_datetime(historical_data['t'], unit='ms')
        historical_data.sort_values("date")
        historical_data.set_index('date', inplace=True)
        historical_data.rename(columns={'o': 'Open', 'h': 'High', 'l': 'Low', 'c': 'Close'}, inplace=True)
        return historical_data