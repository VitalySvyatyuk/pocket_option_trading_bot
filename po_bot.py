import requests
import time

BASE_URL = 'https://pocketoption.com'
LENGTH_STACK_MIN = 460
LENGTH_STACK_MAX = 1000
PERIOD = 60
TIME = 1
SMA_LONG = 50
SMA_SHORT = 8
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

STACK = {}
ACTIONS = {}

def calculate_sma(prices, period):
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period

def calculate_rsi(prices, period):
    if len(prices) < period:
        return None
    gains = 0
    losses = 0
    for i in range(1, period + 1):
        change = prices[-i] - prices[-(i + 1)]
        if change > 0:
            gains += change
        else:
            losses -= change
    avg_gain = gains / period
    avg_loss = losses / period
    rs = avg_gain / avg_loss if avg_loss != 0 else float('inf')
    return 100 - (100 / (1 + rs))

def should_open_trade(sma_short, sma_long, rsi):
    if sma_short > sma_long and rsi < RSI_OVERSOLD:
        return 'buy'
    elif sma_short < sma_long and rsi > RSI_OVERBOUGHT:
        return 'sell'
    return None

# Main trading loop
while True:
    # هنا يجب عليك إضافة الكود لجلب الأسعار من API
    prices = []  # قم بملئها بالأسعار الفعلية من البيانات
    current_price = prices[-1] if prices else 0  # استبدل بالسعر الحالي

    sma_short = calculate_sma(prices, SMA_SHORT)
    sma_long = calculate_sma(prices, SMA_LONG)
    rsi_value = calculate_rsi(prices, RSI_PERIOD)

    if sma_short is not None and sma_long is not None and rsi_value is not None:
        trade_signal = should_open_trade(sma_short, sma_long, rsi_value)

        if trade_signal == 'buy':
            # تنفيذ أمر شراء
            print("Executing buy order")
            # ضع الكود هنا لتنفيذ الصفقة
        elif trade_signal == 'sell':
            # تنفيذ أمر بيع
            print("Executing sell order")
            # ضع الكود هنا لتنفيذ الصفقة

    time.sleep(TIME)  # انتظر الوقت المحدد قبل التكرار
