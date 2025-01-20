import os

import matplotlib.pyplot as plt
import mplfinance as mpf
import numpy as np
import pandas as pd
import talib
import yfinance as yf
import seaborn as sns

from settings_handler import ScreeningOptionsHandler


class Screener:
    def __init__(self, screen_key, POLYGON_KEY, handler: ScreeningOptionsHandler, logger):
        self.primary_color = "#06D6A0"
        self.secondary_color = "#FFC43D"
        
        self.screen_key = screen_key
        self.handler = handler
        self.logger = logger
        self.POLYGON_KEY = POLYGON_KEY
        self.SCREEN_PATH = f"data/screen_results/{self.screen_key}"
        self.count = 0
        if os.path.exists(self.SCREEN_PATH) is False:
            os.makedirs(self.SCREEN_PATH)


    def screen(self):
        options = self.handler.get_options()
        self.logger.info(f"Screening starts with key {self.screen_key}")
        self.logger.info(f"Screening options: {list(options.keys())}")
        for option_name, details in options.items():
            active = details.get("active", False)
            if active:
                self.screen_option(option_name, details)


    def screen_option(self, option_name, details):
        self.logger.info(f"Processing option {option_name}")
        option_path = f"{self.SCREEN_PATH}/{option_name}"
        if os.path.exists(option_path) is False:
            os.makedirs(option_path)

        observed_tickers = details.get("observed_tickers", [])
        alerts = details.get("alerts", [])
        alert_names = [alert["name"] for alert in alerts]
        depth = 50
        results = pd.DataFrame(columns=observed_tickers, index=alert_names)
        for ticker in observed_tickers:
            self.ticker_path = f"{option_path}/{ticker}"
            if os.path.exists(self.ticker_path) is False:
                os.makedirs(self.ticker_path)

            if self.count % 4 == 0:
                self.logger.info("Sleeping for 1 minute to avoid rate limit")

            ticker_c = f"{ticker}=X"
            historical_data = yf.download(ticker_c, period=f"{depth}d", interval="1d")

            if historical_data is None:
                self.logger.error(f"Error in fetching data for {ticker}")
                continue

            self.process_data(historical_data)
            mpf.plot(historical_data, type="candle", style="charles", title=f"{ticker} {depth}")
            plt.savefig(os.path.join(self.ticker_path, f"history_{ticker_c}.png"), format="png")
            plt.close()

            # Generating the indicators
            indicators = details.get("indicators", [])
            for indicator in indicators:
                self.logger.info(f"Processing indicator {indicator}")
                self.generate_indicator(indicator, historical_data)

            # Checking for alerts
            alert_results = []
            for alert in alerts:
                self.logger.info(f"Processing alert {alert}")
                alert_results.append(self.generate_alert(alert, historical_data))

            results[ticker] = alert_results

            historical_data.to_csv(os.path.join(self.ticker_path, f"{ticker_c}.csv"))
            results.to_csv(os.path.join(option_path, "results.csv"))
            self.logger.info(f"Data fetched for {ticker}")

            self.count += 1


    def process_data(self, data):

        data.columns = [col[0] for col in data.columns]
        curr_value = data.iloc[-1]["Close"]

        #Shift the data by 1 to get the next day's close (yFinance bug)
        data["Close"] = data["Open"].shift(-1)
        data.loc[data.index[-1], "Close"] = curr_value

        return data


    def generate_indicator(self, indicator, data):
        params = indicator.get("params", {})
        name = indicator.get("name", "")
        if indicator["type"] == "sma":

            if name == "":
                self.logger.error("Indicator name is required")
                return

            width = params.get("width", 9)
            sma_series = self.calculate_sma(data, width)
            data[name] = sma_series
        elif indicator["type"] == "adx":
            length = indicator.get("length", 14)
            adx_series = talib.ADX(data["High"], data["Low"], data["Close"], timeperiod=length)
            data[name] = adx_series

    def generate_alert(self, alert, data):
        params = alert.get("params", {})
        if alert["type"] == "crossover":
            depth = alert.get("depth", 1)
            indicators = params.get("indicators", [])
            self.logger.info(f"Checking crossover for {indicators}")
            crossover_data = data[indicators[0]] > data[indicators[1]]

            result = 1 if crossover_data[-depth:].all() and not crossover_data[-depth-1]else 0
            if result:
                self.plot_crossover(alert, data)

            return result

        elif alert["type"] == "threshold":
            depth = alert.get("depth", 1)
            threshold = params.get("threshold", 0)
            name = params.get("indicators", [])[0]
            self.logger.info(f"Checking threshold for {name}")
            threshold_data = data[name] > threshold

            return 1 if threshold_data[-depth:].all() else 0
        return 0

    def calculate_sma(self, data: pd.DataFrame, width: int):
        sma_series = data["Close"].rolling(window=width, min_periods=1).mean()
        sma_series[:width] = np.nan
        return sma_series

    def plot_crossover(self, alert, data):
        indicators = alert["params"]["indicators"]
        plt.figure(figsize=(10,8))
        sns.lineplot(data=data, x=data.index, y=indicators[0], label=indicators[0], color=self.primary_color)
        sns.lineplot(data=data, x=data.index, y=indicators[1], label=indicators[1], color=self.secondary_color)
        plt.title(alert.get("name", ""), fontsize=16)
        plt.xlabel('Date', fontsize=14)
        plt.ylabel('Price', fontsize=10)
        plt.grid(True)
        plt.legend()
        plt.xticks(rotation=30)
        plt.savefig(os.path.join(self.ticker_path, f"{alert['name']}.png"), format="png")
