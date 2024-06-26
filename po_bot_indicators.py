import base64
import json
import os
from datetime import datetime, timedelta
from decimal import Decimal

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from stock_indicators import indicators
from stock_indicators.indicators.common.quote import Quote

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

options = Options()
options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
options.add_argument('--ignore-ssl-errors')
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-certificate-errors-spki-list')
options.add_argument('--user-data-dir=default')
# chromedriver can be downloaded from here: https://googlechromelabs.github.io/chrome-for-testing/

try:
    service = Service(executable_path=r'/Users/vitaly/Downloads/chromedriver-mac-arm64/chromedriver')
    driver = webdriver.Chrome(options=options, service=service)
except Exception as e:
    service = Service()
    driver = webdriver.Chrome(options=options, service=service)

companies = {
    'Apple OTC': '#AAPL_otc',
    'American Express OTC': '#AXP_otc',
    'Boeing Company OTC': '#BA_otc',
    'Johnson & Johnson OTC': '#JNJ_otc',
    "McDonald's OTC": '#MCD_otc',
    'Tesla OTC': '#TSLA_otc',
    'Amazon OTC': 'AMZN_otc',
    'VISA OTC': 'VISA_otc',
    'Netflix OTC': 'NFLX_otc',
    'Alibaba OTC': 'BABA_otc',
    'ExxonMobil OTC': '#XOM_otc',
    'FedEx OTC': 'FDX_otc',
    'FACEBOOK INC OTC': '#FB_otc',
    'Pfizer Inc OTC': '#PFE_otc',
    'Intel OTC': '#INTC_otc',
    'TWITTER OTC': 'TWITTER_otc',
    'Microsoft OTC': '#MSFT_otc',
    'Cisco OTC': '#CSCO_otc',
    'Citigroup Inc OTC': 'CITI_otc',
}


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
            print(f"date: {datetime.now().strftime('%H:%M:%S')} do {signal.upper()}, currency: {CURRENCY} last_value: {last_value}")
            driver.find_element(by=By.CLASS_NAME, value=f'btn-{signal}').click()
            ACTIONS[datetime.now()] = last_value
            IS_AMOUNT_SET = False
        except Exception as e:
            print(e)


def get_quotes():
    quotes = []
    for candle in CANDLES:
        open = candle[1]
        close = candle[2]
        high = candle[3]
        low = candle[4]
        if os.name == 'nt':  # windows
            quotes.append(Quote(
                date=datetime.fromtimestamp(candle[0]),
                open=str(open).replace('.', ','),
                high=str(high).replace('.', ','),
                low=str(low).replace('.', ','),
                close=str(close).replace('.', ','),
                volume=None))
        else:
             quotes.append(Quote(
                date=datetime.fromtimestamp(candle[0]),
                open=open,
                high=high,
                low=low,
                close=close,
                volume=None))
    return quotes


def check_indicators():
    quotes = get_quotes()
    psar = indicators.get_parabolic_sar(quotes)
    awesome_oscillator = indicators.get_awesome(quotes, fast_periods=2, slow_periods=34)
    marubozu = indicators.get_marubozu(quotes)
    supertrend = indicators.get_super_trend(quotes)
    sma_long = indicators.get_sma(quotes, lookback_periods=7)
    sma_short = indicators.get_sma(quotes, lookback_periods=3)
    fractal = indicators.get_fractal(quotes, )
    macd = indicators.get_macd(quotes)

    if psar[-1].is_reversal:
        if quotes[-1].close > quotes[-1].open:
            do_action('put')
        elif quotes[-1].close < quotes[-1].open:
            do_action('call')

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
                        check_indicators()
                        CANDLES.append([tstamp, current_value, current_value, current_value, current_value])
            except:
                pass


if __name__ == '__main__':
    load_web_driver()
    while True:
        websocket_log()
