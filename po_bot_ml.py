import base64
import json
from datetime import datetime, timedelta

import pandas as pd
from selenium.webdriver.common.by import By
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from stock_indicators import indicators

from utils import get_driver, get_quotes, get_value

BASE_URL = 'https://pocketoption.com'  # change if PO is blocked in your country
PERIOD = 0  # PERIOD on the graph in seconds, one of: 5, 10, 15, 30, 60, 300 etc.
TIME = 1  # minutes
CANDLES = []
ACTIONS = {}  # dict of {datetime: value} when an action has been made
MAX_ACTIONS = 1  # how many actions allowed at the period of time
ACTIONS_SECONDS = PERIOD  # how long action still in ACTIONS
LAST_REFRESH = datetime.now()
CURRENCY = None
CURRENCY_CHANGE = False
CURRENCY_CHANGE_DATE = datetime.now()
HEADER = [
    # 'supertrend',
    'awesome_oscillator',
    'psar',
    'cci',
    'macd',
    'profit',
]

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


def get_data(quotes, only_last_row=False):
    supertrend = indicators.get_super_trend(quotes)
    awesome_oscillator = indicators.get_awesome(quotes)
    psar = indicators.get_parabolic_sar(quotes)
    cci = indicators.get_cci(quotes)
    macd = indicators.get_macd(quotes)

    data = []
    for i in range(40, len(quotes), 1):
        try:
            row = []
            if only_last_row:
                i = -1
            # row.append(1 if supertrend[i].upper_band else 0)  # not working on Windows non-en_US locale
            row.append(1 if awesome_oscillator[i].oscillator >= 0 else 0)
            row.append(1 if psar[i].is_reversal else 0)
            row.append(1 if cci[i].cci <= 0 else 0)
            row.append(1 if macd[i].macd >= macd[i].signal else 0)
            if only_last_row:
                return [row]
            row.append(1 if get_value(quotes[i + TIME]) <= get_value(quotes[i]) else 0)  # profit
            data.append(row)
        except:
            pass

    return data


def check_data():
    quotes = get_quotes(CANDLES)

    data = get_data(quotes[-200:])
    df = pd.DataFrame(data, columns=HEADER)
    X = df.iloc[:, :len(HEADER) - 1]
    y = df['profit']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=400)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    model_accuracy = accuracy_score(y_test, y_pred)
    last = pd.DataFrame(get_data(quotes, only_last_row=True), columns=HEADER[:-1])
    probe = model.predict_proba(last)
    print('Model accuracy:', round(model_accuracy, 2),
          'PUT probability:', round(probe[0][0], 2),
          'CALL probability:', round(probe[0][1], 2))

    # if model_accuracy > 0.50:
    if probe[0][0] > 0.60:
        do_action('put')
    elif probe[0][1] > 0.60:
        do_action('call')
    else:
        print(quotes[-1].date, 'working...')


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
                    elif value < CANDLES[-1][4]:  # set low
                        CANDLES[-1][4] = value
                    if tstamp % PERIOD == 0:
                        if tstamp not in [c[0] for c in CANDLES]:
                            CANDLES.append([tstamp, value, value, value, value])
                print('Got', len(CANDLES), 'candles for', data['asset'])
            try:
                current_value = data[0][2]
                CANDLES[-1][2] = current_value  # set close all the time
                if current_value > CANDLES[-1][3]:  # set high
                    CANDLES[-1][3] = current_value
                elif current_value < CANDLES[-1][4]:  # set low
                    CANDLES[-1][4] = current_value
                tstamp = int(float(data[0][1]))
                if tstamp % PERIOD == 0:
                    if tstamp not in [c[0] for c in CANDLES]:
                        try:
                            check_data()
                        except Exception as e:
                            print(e)
                        CANDLES.append([tstamp, current_value, current_value, current_value, current_value])
            except:
                pass


if __name__ == '__main__':
    load_web_driver()
    while True:
        websocket_log()
