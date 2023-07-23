import base64
import json
import random
from datetime import datetime, timedelta
from decimal import Decimal

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split


LENGTH_STACK_MIN = 1300
LENGTH_STACK_MAX = 4000  # 1 hour
PERIOD = 15  # PERIOD on the graph
STACK = {}  # {1687021970: 0.87, 1687021971: 0.88}
ACTIONS = []  # list of {datetime: value} when an action has been made
MAX_ACTIONS = 1
ACTIONS_SECONDS = 15  # how long action still in ACTIONS
LAST_REFRESH = datetime.now()
CURRENCY = None
CURRENCY_CHANGE = False
CURRENCY_CHANGE_DATE = datetime.now()
HISTORY_TAKEN = False  # becomes True when history is taken. History length is 900-1800
CLOSED_TRADES_LENGTH = 3
HEADER = [
    'val1200', 'val1140', 'val1080', 'val1020', 'val960', 'val900', 'val840', 'val780', 'val720', 'val660',
    'val600', 'val540', 'val480', 'val420', 'val360', 'val300', 'val240', 'val180', 'val120', 'val60',
    'val', 'profit',
]
MODEL = {}  # {model: datetime}
PREVIOUS = 1200
STEP = 60

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


def load_web_driver():
    # TODO: make currency changing smoother
    base_url = "https://pocketoption.com/en/cabinet/demo-quick-high-low/"  # Change the site
    driver.get(base_url)


def change_currency():
    current_symbol = driver.find_element(by=By.CLASS_NAME, value='current-symbol')
    current_symbol.click()
    # time.sleep(random.random())  # 0-1 sec
    currencies = driver.find_elements(By.XPATH, "//li[contains(., '92%')]")
    if currencies:
        # click random currency
        currency = random.choice(currencies)
        # print('Currencies with profit 92%:', len(currencies))
        currency.click()
        current_symbol.click()  # close assets window
    else:
        pass
        # time.sleep(2)


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
            print(f"date: {datetime.now().strftime('%H:%M:%S')} do {signal.upper()}, currency: {CURRENCY} last_price: {list(STACK.values())[-1]}")
            driver.find_element(by=By.CLASS_NAME, value=f'btn-{signal}').click()
            ACTIONS.append(datetime.now())
        except Exception as e:
            print(e)


def get_data(stack):
    values = list(stack.values())
    data = []
    for i in range(PREVIOUS, len(values) + 1, 1):
        try:
            row = []
            for j in range(0, PREVIOUS + STEP, STEP):
                row.append(values[i - j])  # get previous 21 prices
            row.reverse()
            row.append(1 if values[i] >= values[i + STEP] else 0)  # append result: 1 if put success, 0 otherwise
            data.append(row)
        except:
            pass
    return data


def get_last_row(stack):
    values = list(stack.values())
    row = []
    for j in range(0, PREVIOUS + STEP, STEP):
        row.append(values[- j - 1])
    row.reverse()
    return row


def check_prediction(stack):
    data = get_data(stack)  # get previous 20 prices and the current one with profit column
    df = pd.DataFrame(data, columns=HEADER)

    X = df.iloc[:, :21]  # get all prices without profit column
    y = df['profit']  # get only profit column

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    model = LogisticRegression(max_iter=10000)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    model_accuracy = accuracy_score(y_test, y_pred)  # get accuracy
    print(f'Accuracy: {round(model_accuracy, 2)}, len_stack: {len(stack)}')

    df2 = pd.DataFrame([get_last_row(stack), ], columns=HEADER[:-1])  # create df only with the last row
    y_pred = model.predict(df2)  # predict its profit

    if y_pred[-1] == 0:
        print(f'Do call by prediction')
        do_action('call')
    else:
        print(f'Do put by prediction')
        do_action('put')


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
                change_currency()
    except Exception as e:
        pass


def websocket_log(stack):
    try:
        estimated_profit = driver.find_element(by=By.CLASS_NAME, value='estimated-profit-block__text').text
        if estimated_profit != '+92%':
            # print('The profit is less than 92% -> switching to another currency')
            # time.sleep(random.random() * 10)  # 1-10 sec
            # change_currency()  # TODO: enable it
            pass
    except:
        pass

    global CURRENCY, CURRENCY_CHANGE, CURRENCY_CHANGE_DATE, LAST_REFRESH, HISTORY_TAKEN
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
                # check_closed_trades()  # TODO: enable it
                check_prediction(stack)
    return stack


load_web_driver()
while True:
    STACK = websocket_log(STACK)
