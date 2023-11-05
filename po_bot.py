import base64
import json
import random
import time
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


BASE_URL = 'https://pocketoption.com'  # change if PO is blocked in your country
LENGTH_STACK_MIN = 460
LENGTH_STACK_MAX = 1000  # 4000
PERIOD = 5  # PERIOD on the graph
TIME = 1  # quotes
SMA_LONG = 50
SMA_SHORT = 8
PERCENTAGE = 0.91  # create orders more than PERCENTAGE
STACK = {}  # {1687021970: 0.87, 1687021971: 0.88}
ACTIONS = {}  # dict of {datetime: value} when an action has been made
MAX_ACTIONS = 1
ACTIONS_SECONDS = PERIOD - 1  # how long action still in ACTIONS
LAST_REFRESH = datetime.now()
CURRENCY = None
CURRENCY_CHANGE = False
CURRENCY_CHANGE_DATE = datetime.now()
HISTORY_TAKEN = False  # becomes True when history is taken. History length is 900-1800
CLOSED_TRADES_LENGTH = 3
HEADER = [
    # '00',
    # '01', '02', '03', '04', '05', '06', '07', '08', '09', '10',
    # '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
    # '21', '22', '23', '24', '25', '26', '27', '28', '29', '30',
    # '31', '32', '33', '34', '35', '36', '37', '38', '39', '40',
    # '41', '42', '43', '44', '45', '46', '47', '48', '49', '50',
    'adx',
    'pdi',
    'mdi',
    'rsi',
    'trend',
    'psar',
    'aroon_up',
    'aroon_down',
    'oscillator',
    'vortex_pvi',
    'vortex_nvi',
    'stoch_rsi',
    'stoch_signal',
    'macd',
    'macd_signal',
    'profit',
]
MODEL = None
SCALER = None
PREVIOUS = 1200
MAX_DEPOSIT = 0
MIN_DEPOSIT = 0
INIT_DEPOSIT = None
NUMBERS = {
    '0': '11',
    '1': '7',
    '2': '8',
    '3': '9',
    '4': '4',
    '5': '5',
    '6': '6',
    '7': '1',
    '8': '2',
    '9': '3',
}
IS_AMOUNT_SET = True
AMOUNTS = []  # 1, 3, 8, 18, 39, 82, 172
CURRENT_WINS = 0
MAX_WINS = 15  # in you win 15 times, change a currency
MARTINGALE_COEFFICIENT = 2.0  # everything < 2 have worse profitability
MART = False

options = Options()
options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
options.add_argument('--ignore-ssl-errors')
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-certificate-errors-spki-list')
options.add_argument(r'--user-data-dir=/Users/vitaly/Library/Application Support/Google/Chrome/Default')
# chromedriver can be downloaded from here: https://googlechromelabs.github.io/chrome-for-testing/
service = Service(executable_path=r'/Users/vitaly/Downloads/chromedriver-mac-arm64/chromedriver')
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
ORDERS = []
PUTS = []
CALLS = []


def load_web_driver():
    url = f'{BASE_URL}/en/cabinet/demo-quick-high-low/'
    driver.get(url)


def change_currency():
    current_symbol = driver.find_element(by=By.CLASS_NAME, value='current-symbol')
    current_symbol.click()
    # time.sleep(random.random())  # 0-1 sec
    currencies = driver.find_elements(By.XPATH, "//li[contains(., '92%')]")
    # filtered_currencies = []
    #
    # for currency in currencies:
    #     if CURRENCY not in currency.text:
    #         filtered_currencies.append(currency)

    if currencies:
        # click random currency
        while True:
            currency = random.choice(currencies)
            if CURRENCY not in currency.text:
                break  # avoid repeats
        print('old currency:', CURRENCY, 'new currency:', currency.text)
        currency.click()
    else:
        pass


def do_action(signal):
    action = True
    try:
        last_value = list(STACK.values())[-1]
    except:
        return

    global ACTIONS, IS_AMOUNT_SET
    for dat in list(ACTIONS.keys()):
        if dat < datetime.now() - timedelta(seconds=ACTIONS_SECONDS):
            del ACTIONS[dat]

    if action:
        if len(ACTIONS) >= MAX_ACTIONS:
            # print(f"Max actions reached, don't do a {signal} action")
            action = False

    if action:
        if ACTIONS:
            if signal == 'call' and last_value >= min(list(ACTIONS.values())):
                action = False
            elif signal == 'put' and last_value <= max(list(ACTIONS.values())):
                action = False

    if action:
        try:
            print(f"date: {datetime.now().strftime('%H:%M:%S')} do {signal.upper()}, currency: {CURRENCY} last_value: {last_value}")
            driver.find_element(by=By.CLASS_NAME, value=f'btn-{signal}').click()
            ACTIONS[datetime.now()] = last_value
            IS_AMOUNT_SET = False
        except Exception as e:
            print(e)


def hand_delay():
    time.sleep(0.2)
    # time.sleep(random.choice([0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]))


def get_amounts(amount):
    # if amount > 1999:
    # amounts = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 999]
    # amounts = [1, 3, 5, 12, 25, 51, 104, 215, 438, 888]
    # amounts = [1, 4, 9, 20, 42, 89, 187, 391, 817]
    # amounts = [4, 10, 30, 80, 200, 450, 999]
    amounts = [77, 1, 2, 5, 11, 24, 52, 108, 225, 460, 980]
    print('Amounts:', amounts, 'init deposit:', INIT_DEPOSIT)
    return amounts
    # amounts = []
    # while True:
    #     amount = int(amount / MARTINGALE_COEFFICIENT)
    #     amounts.insert(0, amount)
    #     if amounts[0] <= 1:
    #         amounts[0] = 1
    #         print('Amounts:', amounts, 'init deposit:', INIT_DEPOSIT)
    #         return amounts


def check_indicators(stack):
    # rename function name
    # rm actions
    # use 1 also
    # refactor logic without IS_AMOUNT_SET

    global IS_AMOUNT_SET, AMOUNTS, INIT_DEPOSIT, CURRENT_WINS, ORDERS, PUTS, CALLS, MART

    tim = datetime.now()

    if len(PUTS) + len(CALLS) >= len(ORDERS) + 2:
        print(tim, 'draw all lists, as they are not in sync')
        PUTS, CALLS, ORDERS = [], [], []

    if len(PUTS) > 0 and PUTS[-1][0] == (tim - timedelta(seconds=5)).strftime('%H:%M:%S'):
        if PUTS[-1][1] > list(stack.values())[-1]:  # win
            ORDERS.append(1)
        elif PUTS[-1][1] < list(stack.values())[-1]:  # loose
            ORDERS.append(-1)
        else:  # draw
            ORDERS.append(0)
    elif len(CALLS) > 0 and CALLS[-1][0] == (tim - timedelta(seconds=5)).strftime('%H:%M:%S'):
        if CALLS[-1][1] < list(stack.values())[-1]:  # win
            ORDERS.append(1)
        elif CALLS[-1][1] > list(stack.values())[-1]:  # loose
            ORDERS.append(-1)
        else:  # draw
            ORDERS.append(0)

    try:
        deposit = driver.find_element(by=By.CSS_SELECTOR, value='body > div.wrapper > div.wrapper__top > header > div.right-block > div.right-block__item.js-drop-down-modal-open > div > div.balance-info-block__data > div.balance-info-block__balance > div')
    except Exception as e:
        print(e)

    if not INIT_DEPOSIT:
        INIT_DEPOSIT = float(deposit.text)

    if not AMOUNTS:  # only for init purpose
        AMOUNTS = get_amounts(float(deposit.text))


    if not IS_AMOUNT_SET:
        if len(PUTS) + len(CALLS) == len(ORDERS):
            try:
                amount = driver.find_element(by=By.CSS_SELECTOR, value='#put-call-buttons-chart-1 > div > div.blocks-wrap > div.block.block--bet-amount > div.block__control.control > div.control__value.value.value--several-items > div > input[type=text]')
                amount_value = int(amount.get_attribute('value')[1:])
                base = '#modal-root > div > div > div > div > div.virtual-keyboard.js-virtual-keyboard > div > div:nth-child(%s) > div'

                if ORDERS[-1] == 1:  # win
                    if amount_value != AMOUNTS[0]:
                    # if amount_value > 1:
                        amount.click()
                        for number in str(AMOUNTS[0]):
                            driver.find_element(by=By.CSS_SELECTOR, value=base % NUMBERS[number]).click()
                            hand_delay()
                        AMOUNTS = get_amounts(float(deposit.text))  # refresh amounts
                    MART = False
                    print('win, return to AMOUNTS[0]')
                elif ORDERS[-1] == 0:  # draw
                    print('draw, do nothing')
                    pass
                elif MART or ORDERS[-1] == ORDERS[-2] == ORDERS[-3] == -1:
                    MART = True
                    amount.click()
                    time.sleep(random.choice([0.6, 0.7, 0.8, 0.9, 1.0, 1.1]))
                    if amount_value in AMOUNTS and AMOUNTS.index(amount_value) + 1 < len(AMOUNTS):
                        next_amount = AMOUNTS[AMOUNTS.index(amount_value) + 1]
                        for number in str(next_amount):
                            driver.find_element(by=By.CSS_SELECTOR, value=base % NUMBERS[number]).click()
                            hand_delay()
                        print(f'loose, increase to {next_amount}')
                    else:  # reset to first_value
                        # driver.find_element(by=By.CSS_SELECTOR, value=base % NUMBERS['1']).click()
                        for number in str(AMOUNTS[0]):
                            driver.find_element(by=By.CSS_SELECTOR, value=base % NUMBERS[number]).click()
                            hand_delay()
                        hand_delay()
                        print('loose, change to AMOUNTS[0]')
                hand_delay()
                driver.find_element(by=By.CSS_SELECTOR, value='#bar-chart > div > div > div.right-widget-container > div > div.widget-slot__header > div.title.flex-centered > span').click()
                IS_AMOUNT_SET = True
            except Exception as e:
                print(e)

    print('Let puts + calls:', len(PUTS) + len(CALLS), 'len orders:', len(ORDERS), 'IS_AMOUNT_SET:', IS_AMOUNT_SET, 'MART:', MART)

    if datetime.now().second % 10 != 0:
        return

    amount = driver.find_element(by=By.CSS_SELECTOR, value='#put-call-buttons-chart-1 > div > div.blocks-wrap > div.block.block--bet-amount > div.block__control.control > div.control__value.value.value--several-items > div > input[type=text]')
    amount_value = int(amount.get_attribute('value')[1:])

    if list(stack.values())[-1] < list(stack.values())[-5]:
        PUTS.append([tim.strftime('%H:%M:%S'), list(stack.values())[-1]])
        if MART:
            driver.find_element(by=By.CLASS_NAME, value=f'btn-put').click()
        IS_AMOUNT_SET = False
        print(tim, 'Make put order')
    elif list(stack.values())[-1] > list(stack.values())[-5]:
        CALLS.append([tim.strftime('%H:%M:%S'), list(stack.values())[-1]])
        if MART:
            driver.find_element(by=By.CLASS_NAME, value=f'btn-call').click()
        IS_AMOUNT_SET = False
        print(tim, 'Make call order')
    else:
        print(tim, "don't make an action")


def websocket_log(stack):
    try:
        estimated_profit = driver.find_element(by=By.CLASS_NAME, value='estimated-profit-block__text').text
        if estimated_profit != '+92%':
            print('The profit is less than 92% -> switching to another currency')
            time.sleep(random.random() * 10)  # 1-10 sec
            change_currency()
            pass
    except:
        pass

    global CURRENCY, CURRENCY_CHANGE, CURRENCY_CHANGE_DATE, LAST_REFRESH, HISTORY_TAKEN, MODEL, INIT_DEPOSIT
    global CURRENT_WINS
    try:
        current_symbol = driver.find_element(by=By.CLASS_NAME, value='current-symbol').text
        if current_symbol != CURRENCY:
            CURRENCY = current_symbol
            CURRENCY_CHANGE = True
            CURRENCY_CHANGE_DATE = datetime.now()
    except:
        pass

    if CURRENCY_CHANGE and CURRENCY_CHANGE_DATE < datetime.now() - timedelta(seconds=5):
        stack = {}  # drop stack when currency changed
        HISTORY_TAKEN = False  # take history again
        driver.refresh()  # refresh page to cut off unwanted signals
        CURRENCY_CHANGE = False
        MODEL = None
        INIT_DEPOSIT = None
        CURRENT_WINS = 0

    for wsData in driver.get_log('performance'):
        message = json.loads(wsData['message'])['message']
        response = message.get('params', {}).get('response', {})
        if response.get('opcode', 0) == 2 and not CURRENCY_CHANGE:
            payload_str = base64.b64decode(response['payloadData']).decode('utf-8')
            data = json.loads(payload_str)
            if not HISTORY_TAKEN:
                if 'history' in data:
                    stack = {int(d[0]): d[1] for d in data['history']}
                    print(f"History taken for asset: {data['asset']}, period: {data['period']}, len_history: {len(data['history'])}, len_stack: {len(stack)}")
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
                check_indicators(stack)
    return stack


load_web_driver()
while True:
    STACK = websocket_log(STACK)
