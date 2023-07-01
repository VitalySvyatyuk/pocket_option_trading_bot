import base64
import json
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
LENGTH_STACK_MAX = 1800
POWER_STACK = 30  # power of the last candle or growing movement
PERIOD = 15  # PERIOD on the graph
STEP = PERIOD * 2  # seconds !!!DEPRECATED
STACK = {}  # {1687021970: 0.87, 1687021971: 0.88}
ACTIONS = []  # list of {datetime: value} when an action has been made
MAX_ACTIONS = 1
ACTIONS_SECONDS = 20  # how long action still in ACTIONS
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
TREND_STACK = []  # ["up", "down"]
TREND_LENGTH = 2
REVERSE = False
REVERSE_DATE = None
REVERSE_BARS = 5
# VICE_VERSA = False
CLOSED_TRADES_LENGTH = 2
#TODO: implement DEMO

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

    # if action and ACTIONS:  # additional corrected actions in a row
    #     if signal == 'call' and ACTIONS[-1][1] <= STACK[-1][1]:
    #         print("Don't call")
    #         action = False
    #     if signal == 'put' and ACTIONS[-1][1] >= STACK[-1][1]:
    #         print("Don't put")
    #         action = False

    # estimaded_profit = driver.find_element(by=By.CLASS_NAME, value='estimated-profit-block__text').text
    # if estimaded_profit != '+92%':
    #     # print('Profit is less than 92, do nothing')
    #     action = False

    # signal = 'put' if signal == 'call' else 'call'

    # global VICE_VERSA
    # try:
    #     closed_trades = driver.find_elements(by=By.CLASS_NAME, value='centered')
    #     if action and len(closed_trades) >= VICE_VERSA_LENGTH:
    #         vice_versa_should_be_changed = True
    #         for closed_trade in closed_trades[:VICE_VERSA_LENGTH]:
    #             if float(closed_trade.text.replace('$', '')) > 0:  # at least one is positive, don't change
    #                 vice_versa_should_be_changed = False
    #         if vice_versa_should_be_changed:
    #             VICE_VERSA = not VICE_VERSA
    #             print(f'VICE_VERSA now is: {VICE_VERSA}')
    # except Exception as e:
    #     print(f'VICE_VERSA Exception: {e}')

    # if VICE_VERSA:
    #     signal = 'put' if signal == 'call' else 'call'

    if action:
        try:
            # winsound.Beep(440, 300)
            print(f"date: {datetime.now().strftime('%H:%M:%S')} do {signal.upper()}, currency: {CURRENCY} last_price: {list(STACK.values())[-1]}")
            driver.find_element(by=By.CLASS_NAME, value=f'btn-{signal}').click()
            ACTIONS.append(datetime.now())
        except Exception as e:
            print(e)


def update_reverse(long, short):
    global TREND_STACK, REVERSE, REVERSE_DATE, ACTIONS
    if len(TREND_STACK) < TREND_LENGTH:
        if short > long:
            TREND_STACK.append('up')
        elif short < long:
            TREND_STACK.append('down')
        else:  # if equals, append the same last element
            TREND_STACK.append(TREND_STACK[-1])
    elif len(TREND_STACK) > TREND_LENGTH:
        TREND_STACK = []  # refresh
        print('Refresh trend stack')
    if len(TREND_STACK) == TREND_LENGTH:
        if TREND_STACK[0] != TREND_STACK[1]:
            REVERSE = True
        else:
            REVERSE = False
        # for old, new in zip(TREND_STACK[:TREND_LENGTH // 2], TREND_STACK[TREND_LENGTH // 2:]):
        #     if old == new or old != TREND_STACK[0]:
        #         REVERSE = False
        #         break
        if REVERSE:
            print(f'Reverse to {TREND_STACK[-1]}')
            REVERSE_DATE = datetime.now()
            ACTIONS = []  # refresh ACTIONS during reverse # TODO: check this
        TREND_STACK = TREND_STACK[1:]

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
        quotes.append(Quote(date=datetime.fromtimestamp(keys[i]), open=str(open).replace('.', ','), high=str(high).replace('.', ','), low=str(low).replace('.', ','), close=str(close).replace('.', ','), volume=None))
    return quotes

def check_cci_indicator(stack):
    # ### MASS
    # try:
    #     start = driver.find_element(by=By.CLASS_NAME, value='start').text
    #     start = int(start.replace('%', ''))
    # except:
    #     return
    # if start > 97:
    #     print('Do call by MASS')
    #     do_action('call')
    # elif start < 3:
    #     print('Do put by MASS')
    #     do_action('put')
    # return
    # ### MASS END


    ### 10sec Candle
    # 10 sec graph
    # 3 min time
    # sma 14 blue
    # smma 10 white
    # macd 16 26 9
    # wait macd transition CHECK THIS SEPARATELY
    # current candle can't cross white line of smma (down/up) red candle down, green candle up  (but can cross blue sma)
    # macd slow and fast should be above macd for put and below macd for call


    ### 10sec Candle END

    quotes = get_quotes(stack, PERIOD)
    last_value = list(stack.values())[-1]
    sma_long = indicators.get_sma(quotes, lookback_periods=SMA_LONG)
    sma_short = indicators.get_sma(quotes, lookback_periods=SMA_SHORT)
    smma_short = indicators.get_smma(quotes, lookback_periods=SMMA_SHORT)
    # cci_results = indicators.get_cci(quotes, CCI_PERIOD)
    psar = indicators.get_parabolic_sar(quotes)
    macd = indicators.get_macd(quotes, fast_periods=12, slow_periods=26, signal_periods=9)
    adx = indicators.get_adx(quotes)
    rsi = indicators.get_rsi(quotes)

    # try:
    #     # call:
    #     if macd[-1].signal < macd[-1].macd < macd[-1].histogram:
    #         if max(list(stack.values())[-30:]) < smma_short[-1].smma:
    #             # if adx[-1].pdi > adx[-1].mdi:
    #             #     print('ADX is ready')
    #             # else:
    #             #     print('ADX is NOT ready')
    #             if psar[-1].sar < last_value:
    #                 print('PSAR is ready')
    #             else:
    #                 print('PSAR is NOT ready')
    #             print('Do call by SMMA + MACD')
    #             do_action('call')
    #     # put:
    #     elif macd[-1].signal > macd[-1].macd > macd[-1].histogram:
    #         if min(list(stack.values())[-30:]) > smma_short[-1].smma:
    #             # if adx[-1].pdi < adx[-1].mdi:
    #             #     print('ADX is ready')
    #             # else:
    #             #     print('ADX is NOT ready')
    #             if psar[-1].sar > last_value:
    #                 print('PSAR is ready')
    #             else:
    #                 print('PSAR is NOT ready')
    #             print('Do put by SMMA + MACD')
    #             do_action('put')
    # except Exception as e:
    #     print(e)


    # PSAR
    try:
        # print(psar[-1].sar < last_value)
        if psar[-1].is_reversal:
            print('PSAR is reversal')
            if adx[-1].adx > 18:
                print(f'ADX: {adx[-1].adx}, RSI: {rsi[-1].rsi}')
                if psar[-1].sar < last_value:
                    print('Do call by PSAR reversal')
                    if macd[-1].signal < macd[-1].macd < 0:
                        print('Do call by PSAR reversal with MACD')
                        # if rsi[-1].rsi < 50:
                        # print('Do call by PSAR reversal with RSI < 50')
                        do_action('call')
                if psar[-1].sar > last_value:
                    print('Do put by PSAR reversal')
                    if macd[-1].signal > macd[-1].macd > 0:
                        print('Do put by PSAR reversal with MACD')
                        # if rsi[-1].rsi > 50:
                        # print('Do call by PSAR reversal with RSI > 50')
                        do_action('put')
    except Exception as e:
        print(e)
    return
    # PSAR END

    ### MACD
    ### MACD END

    # ### CALC CCI average
    # diff_sum = 0
    # count = 0
    # for i in range(len(cci_results) - 1):
    #     try:
    #         diff_sum += abs(abs(cci_results[i].cci) - abs(cci_results[i+1].cci))
    #         count += 1
    #     except:
    #         pass
    # print(f'Diff sum: {diff_sum // count}')
    # ### ENDCALC CCI average

    # ### TODO: TEST crossing both moving averages
    # # should cross by 3 seconds
    # if list(stack.values())[-4] < list(stack.values())[-1]:
    #     if list(stack.values())[-4] < sma_long[-1].sma and list(stack.values())[-4] < sma_short[-1].sma:
    #         if list(stack.values())[-1] > sma_long[-1].sma and list(stack.values())[-1] > sma_short[-1].sma:
    #             print('Do call')
    #             do_action('call')
    # elif list(stack.values())[-4] > list(stack.values())[-1]:
    #     if list(stack.values())[-4] > sma_long[-1].sma and list(stack.values())[-4] > sma_short[-1].sma:
    #         if list(stack.values())[-1] < sma_long[-1].sma and list(stack.values())[-1] < sma_short[-1].sma:
    #             print('Do put')
    #             do_action('put')
    # ### TODO: END TEST

    # ### TODO: TEST abrupt CCI change
    # diff = abs(abs(cci_results[-2].cci) - abs(cci_results[-1].cci))
    # print(diff, f'cci:', cci_results[-1].cci)
    # if diff > 50:
    # if cci_results[-1].cci > -70 and cci_results[-5].cci < -110 :  # TODO: direction should be checked more precisely
    #     print('Do call by CCI exit -100')
    #     do_action('call')
    # elif cci_results[-1].cci < 70 and cci_results[-5].cci > 110:
    #     print('Do put by CCI exit 100')
    #     do_action('put')
    # return
    # print('Do action by CCI diff')
    # if diff > 40:  # INVERTED
    #     if list(stack.values())[-2] < list(stack.values())[-1] and list(stack.values())[-1] > sma_short[-1].sma:
    #         print('Do call by CCI diff')
    #         do_action('call')
    #     elif list(stack.values())[-2] > list(stack.values())[-1] and list(stack.values())[-1] < sma_short[-1].sma:
    #         print('Do put by CCI diff')
    #         do_action('put')
    #     print(f'Do action by CCI diff: {diff}')
    # ### END TEST
    # return

    # ### TODO: TEST Only cci += CCI delete later
    # print(cci_results[-1].cci)
    # if cci_results[-1].cci > CCI:
    #     do_action('call')
    # elif cci_results[-1].cci < -CCI:
    #     do_action('put')
    # return
    # ### TODO: END TEST

    # if not sma_long[-1].sma or not sma_short[-1].sma or not cci_results[-1].cci:  # TODO: check and remove this if not happens
    #     print(f'sma_long[-1].sma or sma_short[-1].sma or cci_results[-1].cci is None')
    #     return  # it happens with STEP > 30 for 15 sec periods

    # update_reverse(sma_long[-1].sma, sma_short[-1].sma)
    #
    # if REVERSE:
    #     print(f'cci: {cci_results[-1].cci}, TREND STACK: {TREND_STACK}')
    #     pass

    # if cci_results[-1].cci and cci_results[-1].cci > CCI or cci_results[-1].cci < -CCI:
    #     print(f'cci: {int(cci_results[-1].cci)}')

    # signal = None
    # if REVERSE_DATE and REVERSE_DATE > datetime.now() - timedelta(seconds=REVERSE_BARS * PERIOD):
    #     print(f"Trend changed, {REVERSE_DATE.strftime('%H:%M:%S')} -> {(datetime.now() - timedelta(seconds=REVERSE_BARS * PERIOD)).strftime('%H:%M:%S')}, ")  # 'cci:', {int(cci_results[-1].cci)}
    #     if sma_short[-1].sma > sma_long[-1].sma:  # and cci_results[-1].cci > CCI
    #         signal = 'call'
    #     elif sma_short[-1].sma <= sma_long[-1].sma:  # and cci_results[-1].cci < -CCI:
    #         signal = 'put'
    #     if signal:
    #         print(f'Do action {signal}')
    #         do_action(signal)

def check_closed_trades():
    try:
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
                change_currency()
    except Exception as e:
        pass

def WebSocketLog(stack):
    try:
        estimated_profit = driver.find_element(by=By.CLASS_NAME, value='estimated-profit-block__text').text
        if estimated_profit != '+92%':
            # print('The profit is less than 92% -> switching to another currency')
            time.sleep(random.random() * 10)  # 1-10 sec
            change_currency()
    except:
        pass

    global CURRENCY, CURRENCY_CHANGE, CURRENCY_CHANGE_DATE, LAST_REFRESH, TREND_STACK, REVERSE, REVERSE_DATE, HISTORY_TAKEN
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
        TREND_STACK = []
        REVERSE = False
        REVERSE_DATE = None
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
            if not HISTORY_TAKEN and 'history' in data:
                HISTORY_TAKEN = True
                stack = {int(d[0]): d[1] for d in data['history']}
                print(f"History taken for asset: {data['asset']}, period: {data['period']}, len_history: {len(data['history'])}, len_stack: {len(stack)}")
            try:
                current_symbol = driver.find_element(by=By.CLASS_NAME, value='current-symbol').text
                symbol, timestamp, value = data[0]
            except:
                continue
            if current_symbol.replace('/', '').replace(' ', '') != symbol.replace('_', '').upper() and companies.get(current_symbol) != symbol:
                continue

            if len(stack) == LENGTH_STACK_MAX:
                first_element = next(iter(stack))
                del stack[first_element]
            if len(stack) < LENGTH_STACK_MAX:
                if int(timestamp) in stack:  # TODO: remove this for performance
                    return stack  # TODO: remove this and we will win a half of a second
                else:
                    stack[int(timestamp)] = value
            elif len(stack) > LENGTH_STACK_MAX:
                print(f"Len > {LENGTH_STACK_MAX}!!")
                stack = {}  # refresh then
            if len(stack) >= LENGTH_STACK_MIN:
                check_closed_trades()
                # check_psar_indicator(stack)
                check_cci_indicator(stack)
    return stack

LoadWebDriver()
# time.sleep(50)  # delay for typing login and password
while True:
    STACK = WebSocketLog(STACK)


# import matplotlib.pyplot as plt
# x = [x.date for x in cci_results]
# y = [y.cci for y in cci_results]
# plt.plot(x, y, color='blue', linewidth=2)
# plt.show()
