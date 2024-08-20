import base64
import json
import os
from datetime import datetime, timedelta

import pandas as pd
from selenium.webdriver.common.by import By
from stock_indicators import indicators

from utils import get_driver, get_quotes, get_value

BASE_URL = 'https://pocketoption.com'  # change if PO is blocked in your country
PERIOD = 0  # PERIOD on the graph in seconds, one of: 5, 10, 15, 30, 60, 300 etc.
CANDLES = []
ACTIONS = {}  # dict of {datetime: value} when an action has been made
MAX_ACTIONS = 1  # how many actions allowed at the period of time
ACTIONS_SECONDS = PERIOD  # how long action still in ACTIONS
LAST_REFRESH = datetime.now()
CURRENCY = None
CURRENCY_CHANGE = False
CURRENCY_CHANGE_DATE = datetime.now()
SAVE_CSV = False

driver = get_driver()


def load_web_driver():
    url = f'{BASE_URL}/en/cabinet/demo-quick-high-low/'
    driver.get(url)


def do_action(signal):
    action = True
    last_value = CANDLES[-1][2]

    global ACTIONS, IS_AMOUNT_SET
    for dat in list(ACTIONS.keys()):
        if dat < datetime.now() - timedelta(seconds=ACTIONS_SECONDS):
            del ACTIONS[dat]

    if action:
        if len(ACTIONS) >= MAX_ACTIONS:
            # print(f"Max actions reached, don't do a {signal} action")
            action = False

    if action:
        try:
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {signal.upper()}, currency: {CURRENCY} last_value: {last_value}")
            driver.find_element(by=By.CLASS_NAME, value=f'btn-{signal}').click()
            ACTIONS[datetime.now()] = last_value
            IS_AMOUNT_SET = False
        except Exception as e:
            print(e)


def check_indicators():
    quotes = get_quotes(CANDLES)
    sma_long = indicators.get_sma(quotes, lookback_periods=8)
    sma_short = indicators.get_sma(quotes, lookback_periods=3)

    if sma_short[-2].sma > sma_long[-2].sma and sma_short[-1].sma < sma_long[-1].sma:
        if get_value(quotes[-1]) < get_value(quotes[-2]) < get_value(quotes[-3]):
            do_action('put')
    elif sma_short[-2].sma < sma_long[-2].sma and sma_short[-1].sma > sma_long[-1].sma:
        if get_value(quotes[-1]) > get_value(quotes[-2]) > get_value(quotes[-3]):
            do_action('call')
    else:
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'working...')


def websocket_log():
    global CURRENCY, CURRENCY_CHANGE, CURRENCY_CHANGE_DATE, LAST_REFRESH, PERIOD, CANDLES
    try:
        current_symbol = driver.find_element(by=By.CLASS_NAME, value='current-symbol').text
        if current_symbol != CURRENCY:
            CURRENCY = current_symbol
            CURRENCY_CHANGE = True
            CURRENCY_CHANGE_DATE = datetime.now()
    except:
        pass

    if CURRENCY_CHANGE and CURRENCY_CHANGE_DATE < datetime.now() - timedelta(seconds=5):
        driver.refresh()  # refresh page to cut off unwanted signals
        CURRENCY_CHANGE = False
        CANDLES = []
        PERIOD = 0

    for wsData in driver.get_log('performance'):
        message = json.loads(wsData['message'])['message']
        response = message.get('params', {}).get('response', {})
        if response.get('opcode', 0) == 2 and not CURRENCY_CHANGE:
            payload_str = base64.b64decode(response['payloadData']).decode('utf-8')
            data = json.loads(payload_str)
            if 'asset' in data and 'candles' in data:  # 5m
                PERIOD = data['period']
                CANDLES = list(reversed(data['candles']))  # timestamp open close high low
                CANDLES.append([CANDLES[-1][0] + PERIOD, CANDLES[-1][1], CANDLES[-1][2], CANDLES[-1][3], CANDLES[-1][4]])
                for tstamp, value in data['history']:
                    tstamp = int(float(tstamp))
                    CANDLES[-1][2] = value  # set close all the time
                    if value > CANDLES[-1][3]:  # set high
                        CANDLES[-1][3] = value
                    if value < CANDLES[-1][4]:  # set low
                        CANDLES[-1][4] = value
                    if tstamp % PERIOD == 0:
                        if tstamp not in [c[0] for c in CANDLES]:
                            CANDLES.append([tstamp, value, value, value, value])
                if SAVE_CSV:
                    asset = data['asset'].replace('_', '').upper()
                    now = datetime.now()
                    minutes = data['period'] // 60
                    directory = f'data_{minutes}m'
                    os.makedirs(directory, exist_ok=True)
                    filename = f'{directory}/{asset}_{now.year}_{now.month}_{now.day}_{now.hour}.csv'
                    df = pd.DataFrame(CANDLES, columns=['timestamp', 'open', 'close', 'high', 'low'])
                    df.to_csv(filename)
                    print(f'History file saved: {filename}')
                print('Got', len(CANDLES), 'candles for', data['asset'])
            try:
                current_value = data[0][2]
                CANDLES[-1][2] = current_value  # set close all the time
                if current_value > CANDLES[-1][3]:  # set high
                    CANDLES[-1][3] = current_value
                if current_value < CANDLES[-1][4]:  # set low
                    CANDLES[-1][4] = current_value
                tstamp = int(float(data[0][1]))
                if tstamp % PERIOD == 0:
                    if tstamp not in [c[0] for c in CANDLES]:
                        check_indicators()
                        CANDLES.append([tstamp, current_value, current_value, current_value, current_value])
            except:
                pass


if __name__ == '__main__':
    load_web_driver()
    while True:
        websocket_log()
