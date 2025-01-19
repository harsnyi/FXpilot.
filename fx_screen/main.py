from flask import Flask, jsonify
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import uuid
import logging
import pandas as pd
from settings_handler import ScreeningOptionsHandler
from view_screener_settings import create_tickers_bp
from screener import Screener
from logging.handlers import RotatingFileHandler


app = Flask(__name__)
load_dotenv()
POLYGON_KEY = os.getenv('POLYGON_KEY')

handler = ScreeningOptionsHandler('data/screening_options', 'settings_schema.yaml')

tickers_bp = create_tickers_bp(handler)
app.register_blueprint(tickers_bp, url_prefix='/settings')

if os.path.exists('logs') is False:
    os.makedirs('logs')

log_handler = RotatingFileHandler('logs/app.log', maxBytes=10*1024*1024, backupCount=5)
log_handler.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logging.getLogger().addHandler(log_handler)
logging.getLogger().addHandler(console_handler)
logging.getLogger().setLevel(logging.INFO)

@app.route('/screen', methods=['GET'])
def screen_forex():
    screen_key = str(uuid.uuid4())[:8]
    screener = Screener(screen_key, POLYGON_KEY, handler, logger=logging.getLogger())
    screener.screen()

    return jsonify({"message": "Success"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
