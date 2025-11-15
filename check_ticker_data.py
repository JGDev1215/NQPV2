#!/usr/bin/env python3
import requests
import json

response = requests.get('http://localhost:8080/api/data')
data = response.json()

# Check which fields each ticker has
for ticker in ['NQ=F', 'ES=F', '^FTSE']:
    if ticker in data['data']:
        ticker_data = data['data'][ticker]
        print(f'\n{ticker} fields:')
        print(f"  - Has intraday_predictions: {'intraday_predictions' in ticker_data}")
        print(f"  - Has daily_accuracy: {'daily_accuracy' in ticker_data}")

        if 'intraday_predictions' in ticker_data:
            pred = ticker_data['intraday_predictions']
            print(f"    - Has nine_am: {'nine_am' in pred}")
            print(f"    - Has ten_am: {'ten_am' in pred}")
            print(f"    - Predictions locked: {pred.get('predictions_locked', 'N/A')}")
