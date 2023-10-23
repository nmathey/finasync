import requests
from pathlib import Path
from datetime import datetime, timedelta
import json
from json.decoder import JSONDecodeError

from .constants import EXCHANGE_RATES_API_URI, EXCHANGE_OFFLINE_RATES

def convert_currency(amount, from_currency, to_currency):
    Now_Time = datetime.today()
    Exchange_OfflineRates_Path = Path(EXCHANGE_OFFLINE_RATES)
    Exchange_OfflineRates_Path.touch(exist_ok=True)
    converted_amount = 0
    with open(Exchange_OfflineRates_Path) as json_file:
        try:
            Exchange_OfflineRates = json.load(json_file)
        except JSONDecodeError:
            Exchange_OfflineRates = {
                "info": {
                    "last_sync": str(datetime.timestamp(Now_Time - timedelta(weeks=2)))
                },
                "data": {}
            }

    # Fetch latest exchange rates only if local cache > 1 week
    if float(Exchange_OfflineRates["info"]["last_sync"]) < datetime.timestamp(Now_Time - timedelta(weeks=1)):
        response = requests.get(EXCHANGE_RATES_API_URI + to_currency)
        Exchange_OfflineRates["info"]["last_sync"] = str(datetime.timestamp(Now_Time))
        Exchange_OfflineRates["data"] = response.json()

    data = Exchange_OfflineRates["data"]
    if 'rates' in data:
        rates = data['rates']
        if from_currency in rates and to_currency in rates:
            converted_amount = amount / rates[from_currency]
        else:
            raise ValueError("Invalid currency!")
    else:
        raise ValueError("Unable to fetch exchange rates!")
    
    with open(Exchange_OfflineRates_Path, 'w') as outfile:
        json.dump(Exchange_OfflineRates, outfile, indent=4)
    
    return round(converted_amount, 2)