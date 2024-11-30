from datetime import datetime

from stock_indicators.indicators.common.quote import Quote


def get_quotes(candles):
    quotes = []
    for candle in candles:
        open = candle[1]
        close = candle[2]
        high = candle[3]
        low = candle[4]

        try:
            quotes.append(Quote(
                date=datetime.fromtimestamp(candle[0]),
                open=open,
                high=high,
                low=low,
                close=close,
                volume=None))
        except ValueError:  # on Windows and non-en_US locale
            quotes.append(Quote(
                date=datetime.fromtimestamp(candle[0]),
                open=str(open).replace('.', ','),
                high=str(high).replace('.', ','),
                low=str(low).replace('.', ','),
                close=str(close).replace('.', ','),
                volume=None))

    return quotes


def get_value(quote, param='close'):
    # normally, quotes[-1].close works on MacOs, Linux and Windows with 'en_US' locale
    # this method is for Windows with other locales

    try:
        value = getattr(quote, param)
    except Exception as e:
        try:
            value = float(str(getattr(quote, param.capitalize())).replace(',', '.'))
        except Exception as e:
            return None
    return value
