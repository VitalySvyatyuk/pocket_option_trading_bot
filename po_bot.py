import base64
import json
import os
import random
import time
# import winsound

from datetime import datetime, timedelta
from decimal import Decimal
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from stock_indicators import indicators
from stock_indicators.indicators.common.quote import Quote

LENGTH_STACK_MIN = 450
LENGTH_STACK_MAX = 5000
PERIOD = 15  # PERIOD on the graph
STACK = {}  # {1687021970: 0.87, 1687021971: 0.88}
ACTIONS = []  # list of {datetime: value} when an action has been made
MAX_ACTIONS = 1
ACTIONS_SECONDS = 10  # how long action still in ACTIONS
LAST_REFRESH = datetime.now()
CURRENCY = None
CURRENCY_CHANGE = False
CURRENCY_CHANGE_DATE = datetime.now()
HISTORY_TAKEN = False  # becomes True when history is taken. History length is 900-1800
SMA_LONG = 60
SMA_SHORT = 4
SMMA_SHORT = 10
CCI_PERIOD = 20
CCI = 100
CLOSED_TRADES_LENGTH = 2
TREND_LENGTH = 15
TREND_STACK = []
TREND = 'unknown'  # up, down
TREND_INIT_CHANGE = True

options = Options()
options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
driver = webdriver.Chrome(options=options)

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


def LoadWebDriver():
    # TODO: make currency changing smoother
    base_url = "https://pocketoption.com/en/cabinet/demo-quick-high-low/"  # Change the site
    driver.get(base_url)


def change_currency():
    driver.find_element(by=By.CLASS_NAME, value='current-symbol').click()
    time.sleep(random.random())  # 0-1 sec
    currencies = driver.find_elements(By.XPATH, "//li[contains(., '92%')]")
    if currencies:
        # click random currency
        currency = random.choice(currencies)
        # print('Currencies with profit 92%:', len(currencies))
        currency.click()
    else:
        time.sleep(2)


def do_action(signal):
    action = True
    # update ACTIONS:
    global ACTIONS
    for ACTION in ACTIONS:
        if ACTION < datetime.now() - timedelta(seconds=ACTIONS_SECONDS):
            ACTIONS.remove(ACTION)

    if action:
        if len(ACTIONS) >= MAX_ACTIONS:
            # print(f"Max actions reached, don't do a {signal} action")
            action = False

    if action:
        try:
            # winsound.Beep(440, 300)
            print(f"date: {datetime.now().strftime('%H:%M:%S')} do {signal.upper()}, currency: {CURRENCY} last_price: {list(STACK.values())[-1]}")
            driver.find_element(by=By.CLASS_NAME, value=f'btn-{signal}').click()
            ACTIONS.append(datetime.now())
        except Exception as e:
            print(e)


def get_quotes(stack, step=1):
    if len(stack) // 100 == len(stack) / 100 and len(stack) < LENGTH_STACK_MAX:
        print(len(stack))
    quotes = []
    quotes_length = (len(stack) // step) * step  # 507 to 505

    keys = list(stack.keys())
    values = list(stack.values())

    for i in range(len(stack) - quotes_length, len(stack), step):
        open = values[i]
        close = values[i + step - 1]
        high = max(values[i:i + step - 1])
        low = min(values[i:i + step - 1])
        if os.name == 'nt':  # windows
            quotes.append(Quote(
                date=datetime.fromtimestamp(keys[i]),
                open=str(open).replace('.', ','),
                high=str(high).replace('.', ','),
                low=str(low).replace('.', ','),
                close=str(close).replace('.', ','),
                volume=None))
        else:
             quotes.append(Quote(
                date=datetime.fromtimestamp(keys[i]),
                open=open,
                high=high,
                low=low,
                close=close,
                volume=None))
    return quotes


def get_trend(supertrend):
    global TREND_STACK, TREND
    if len(TREND_STACK) < TREND_LENGTH:
        if supertrend[-1].upper_band is None:
            TREND_STACK.append('up')
        else:
            TREND_STACK.append('down')
    if len(TREND_STACK) == TREND_LENGTH:
        if TREND_STACK.count(TREND_STACK[0]) == len(TREND_STACK):
            TREND = TREND_STACK[0]  # ether up or down
        else:
            TREND = 'unknown'  # up, down
        del TREND_STACK[0]
    elif len(TREND_STACK) > TREND_LENGTH:
        TREND_STACK = []  # refresh


def check_indicators(stack):
    global TREND_INIT_CHANGE
    quotes = get_quotes(stack, PERIOD)
    last_value = list(stack.values())[-1]
    # sma_long = indicators.get_sma(quotes, lookback_periods=SMA_LONG)
    # sma_short = indicators.get_sma(quotes, lookback_periods=SMA_SHORT)
    # smma_short = indicators.get_smma(quotes, lookback_periods=SMMA_SHORT)
    # cci_results = indicators.get_cci(quotes, CCI_PERIOD)
    # psar = indicators.get_parabolic_sar(quotes)
    # macd = indicators.get_macd(quotes, fast_periods=12, slow_periods=26, signal_periods=9)
    # adx = indicators.get_adx(quotes)
    # rsi = indicators.get_rsi(quotes)
    supertrend = indicators.get_super_trend(quotes)
    trend_before = TREND
    # print(f'Trend before: {trend_before}')
    get_trend(supertrend)
    trend_after = TREND
    print(TREND_STACK)
    # print(f'Trend after: {trend_after}')

    # trend is strong and rsi between 70 and 50 for call
    # rsi 50-30 with down - do put

    # trend is strong and rsi > 30 for call

    # also call rsi between 70 and 50 for strong up trend

    # if macd[-1].macd > 1 or macd[-1].macd < -1:
    #     print('Inadequate MACD, pass')
    #     return
    # print(f'trend: {"up" if supertrend[-1].lower_band else "down"}')
    try:
        # if trend_before != trend_after:
        #     if TREND_INIT_CHANGE:  # pass init trend change
        #         TREND_INIT_CHANGE = False
        #         return
        #     print(f'Trend is changed to {TREND}')
        #     if trend_after == 'up':
        #         print(f'Do call by supertrend')
        #         do_action('call')
        #     elif trend_after == 'down':
        #         print(f'Do put by supertrend')
        #         do_action('put')
        if last_value < list(stack.values())[-15]:
            print(f'Do call by supertrend')
            do_action('call')
        else:
            print(f'Do put by supertrend')
            do_action('put')
    except Exception as e:
        print(e)


def check_closed_trades():
    try:
        closed_tab = driver.find_element(by=By.CSS_SELECTOR, value='#bar-chart > div > div > div.right-widget-container > div > div.widget-slot__header > div.divider > ul > li:nth-child(2) > a')
        closed_tab_parent = closed_tab.find_element(by=By.XPATH, value='..')
        if closed_tab_parent.get_attribute('class') == '':
            closed_tab_parent.click()
        closed_trades = driver.find_elements(by=By.CLASS_NAME, value='centered')
        closed_trades_currencies = driver.find_elements(by=By.CLASS_NAME, value='deals-list__item')
        if len(closed_trades) >= CLOSED_TRADES_LENGTH:
            minus_trades = 0
            for i, closed_trade in enumerate(closed_trades[:CLOSED_TRADES_LENGTH]):
                if '$0.00' in closed_trade.text:
                    if CURRENCY in closed_trades_currencies[i].text:
                        minus_trades += 1
            if minus_trades == CLOSED_TRADES_LENGTH:
                # winsound.Beep(880, 100)
                # change_currency()
                pass
    except Exception as e:
        pass


def WebSocketLog(stack):
    # try:
    #     estimated_profit = driver.find_element(by=By.CLASS_NAME, value='estimated-profit-block__text').text
    #     if estimated_profit != '+92%':
    #         # print('The profit is less than 92% -> switching to another currency')
    #         time.sleep(random.random() * 10)  # 1-10 sec
    #         change_currency()
    # except:
    #     pass

    global CURRENCY, CURRENCY_CHANGE, CURRENCY_CHANGE_DATE, LAST_REFRESH, HISTORY_TAKEN, TREND_STACK
    try:
        current_symbol = driver.find_element(by=By.CLASS_NAME, value='current-symbol').text
        if current_symbol != CURRENCY:
            CURRENCY = current_symbol
            CURRENCY_CHANGE = True
            CURRENCY_CHANGE_DATE = datetime.now()
            # print(f'Currency changed to {current_symbol}')
    except:
        pass

    if CURRENCY_CHANGE and CURRENCY_CHANGE_DATE < datetime.now() - timedelta(seconds=5):
        stack = {}  # drop stack when currency changed
        HISTORY_TAKEN = False  # take history again
        driver.refresh()  # refresh page to cut off unwanted signals
        CURRENCY_CHANGE = False
        TREND_STACK = []
        # print('currency_change is False')

    for wsData in driver.get_log('performance'):
        message = json.loads(wsData['message'])['message']
        response = message.get('params', {}).get('response', {})
        if response.get('opcode', 0) == 2 and not CURRENCY_CHANGE:
            payload_str = base64.b64decode(response['payloadData']).decode('utf-8')
            data = json.loads(payload_str)
            if not HISTORY_TAKEN:
                if 'asset' in data and 'data' in data:
                    HISTORY_TAKEN = True
                    stack = {int(d['time']): d['price'] for d in data['data']}
                    print(f"History taken for asset: {data['asset']}, period: {data['period']}, len_history: {len(data['data'])}, len_stack: {len(stack)}")
                # if 'history' in data:
                #     stack = {int(d[0]): d[1] for d in data['history']}
                #     print(f"History taken for asset: {data['asset']}, period: {data['period']}, len_history: {len(data['history'])}, len_stack: {len(stack)}")
            try:
                current_symbol = driver.find_element(by=By.CLASS_NAME, value='current-symbol').text
                symbol, timestamp, value = data[0]
            except:
                continue
            try:
                if current_symbol.replace('/', '').replace(' ', '') != symbol.replace('_', '').upper() and companies.get(current_symbol) != symbol:
                    continue
            except:
                pass

            if len(stack) == LENGTH_STACK_MAX:
                first_element = next(iter(stack))
                del stack[first_element]
            if len(stack) < LENGTH_STACK_MAX:
                if int(timestamp) in stack:
                    return stack
                else:
                    stack[int(timestamp)] = value
            elif len(stack) > LENGTH_STACK_MAX:
                print(f"Len > {LENGTH_STACK_MAX}!!")
                stack = {}  # refresh then
            if len(stack) >= LENGTH_STACK_MIN:
                check_closed_trades()
                check_indicators(stack)
    return stack

LoadWebDriver()
while True:
    STACK = WebSocketLog(STACK)
