from settings_handler import ScreeningOptionsHandler
import os
from datetime import datetime, timedelta
import requests
from utils import get_ticker_history
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
import numpy as np

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
        alerts = details.get('alerts', [])
        alert_names = [alert['name'] for alert in alerts]
        depth = 50
        today = datetime.now()
        results = pd.DataFrame(columns=observed_tickers, index=alert_names)
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
                
                # Generating the indicators
                indicators = details.get('indicators', [])
                for indicator in indicators:
                    self.logger.info(f"Processing indicator {indicator}")
                    self.generate_indicator(indicator, historical_data)
                
                # Check for alerts
                alert_results = []
                for alert in alerts:
                    self.logger.info(f"Processing alert {alert}")
                    alert_results.append(self.generate_alert(alert, historical_data))
                
                results[ticker] = alert_results
                
                historical_data.to_csv(os.path.join(option_path, f'{ticker_c}.csv'))
                results.to_csv(os.path.join(option_path, 'results.csv'))
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
    
    
    def generate_indicator(self, indicator, data):
        if indicator["type"] == 'sma':
            name = indicator.get('name', '')
            if name == '':
                self.logger.error("Indicator name is required")
                return
            
            params = indicator.get('params', {})
            width = params.get('width', 9)
            sma_series = self.calculate_SMA(data, width)
            data[name] = sma_series

    def generate_alert(self, alert, data):
        if alert["type"] == 'crossover':
            params = alert.get('params', {})
            depth = alert.get('depth', 1)
            indicators = params.get('indicators', [])
            self.logger.info(f"Checking crossover for {indicators}")
            crossover_data = data[indicators[0]] > data[indicators[1]]

            if crossover_data[-depth:].all():
                return 1  
            
    def calculate_SMA(self, data: pd.DataFrame, width: int):
        sma_series = data["Close"].rolling(window=width, min_periods=1).mean()
        sma_series[:width] = np.nan
        return sma_series