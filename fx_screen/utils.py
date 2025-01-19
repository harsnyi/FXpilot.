
def get_ticker_history(ticker, start_date, today, POLYGON_KEY):
    return f'https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_date.strftime("%Y-%m-%d")}/{today.strftime("%Y-%m-%d")}?adjusted=true&sort=asc&apiKey={POLYGON_KEY}'
