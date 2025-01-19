from flask import Flask, jsonify
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import uuid
import logging
import pandas as pd
from view_screener_settings import tickers_bp

app = Flask(__name__)
load_dotenv()
POLYGON_KEY = os.getenv('POLYGON_KEY')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Register the Blueprint
app.register_blueprint(tickers_bp, url_prefix='/settings')

@app.route('/screen', methods=['GET'])
def screen_forex():
    screen_key = str(uuid.uuid4())[:8]
    app.logger.info(f"Screening starts with key {screen_key}")

    today = datetime.now()
    start_date = today - timedelta(days=50)
    ticker = "C:EURUSD"
    response = requests.get(f'https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_date.strftime("%Y-%m-%d")}/{today.strftime("%Y-%m-%d")}?adjusted=true&sort=asc&apiKey={POLYGON_KEY}')
    if response.status_code == 200:
        
        response = response.json()
        print(response)
        data = response.get('results', None)
        if data:
            app.logger.info(f"Data retrieved for {ticker}")
            historical_data = pd.DataFrame(data)
            historical_data['date'] = pd.to_datetime(historical_data['t'], unit='ms')
            print(historical_data.head())
            
            
        
        return jsonify({"message": "Success"}), 200
    else:
        print(response.text)
        return jsonify({"message": "Error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
