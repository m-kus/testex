import requests
import simplejson as json
from cachetools import TTLCache, cached

from core.helpers import obj_dropna
from core.poloniex.types import PoloniexApiError, PoloniexErrorMessage


class PoloniexRawRequest:
    base_url = 'https://poloniex.com/public'

    def get_response(self, response: requests.Response):
        return response

    def request(self, **params):
        res = requests.get(
            url=self.base_url,
            headers={'content-Type': 'application/json'},
            params=obj_dropna(params)
        )
        return self.get_response(res)

    def __getattr__(self, command):
        def method(**kwargs):
            return self.request(command=command, **kwargs)

        return method


class PoloniexJsonRequest(PoloniexRawRequest):

    def get_response(self, response: requests.Response):
        if response.status_code in [200, 201]:
            data = json.loads(response.text, use_decimal=True)
            if data.get('error'):
                raise PoloniexApiError(data['error'])
        else:
            raise requests.HTTPError(response=response)

        return data


class PoloniexApiProxy:

    def __init__(self):
        self.raw = PoloniexRawRequest()
        self.json = PoloniexJsonRequest()

    @cached(TTLCache(ttl=5, maxsize=128))
    def return_ticker(self):
        return self.raw.returnTicker()

    @cached(TTLCache(ttl=3600, maxsize=128))
    def return_24h_volume(self):
        return self.raw.return24hVolume()

    @cached(TTLCache(ttl=5, maxsize=128))
    def return_order_book(self, currency_pair, depth):
        return self.raw.returnOrderBook(
            currencyPair=currency_pair,
            depth=depth
        )

    @cached(TTLCache(ttl=5, maxsize=128))
    def return_trade_history(self, currency_pair, start, end):
        return self.raw.returnTradeHistory(
            currencyPair=currency_pair,
            start=start,
            end=end
        )

    @cached(TTLCache(ttl=60, maxsize=128))
    def return_chart_data(self, currency_pair, start, end, period):
        return self.raw.returnChartData(
            currencyPair=currency_pair,
            start=start,
            end=end,
            period=period
        )

    @cached(TTLCache(ttl=3600, maxsize=128))
    def return_currencies(self):
        return self.raw.returnCurrencies()

    @cached(TTLCache(ttl=60, maxsize=128))
    def return_loan_orders(self, currency):
        return self.raw.returnLoanOrders(currency=currency)

    @property
    @cached(TTLCache(ttl=60, maxsize=128))
    def tickers(self):
        return self.json.returnTicker()

    @property
    @cached(TTLCache(ttl=3600, maxsize=128))
    def currencies(self):
        return self.json.returnCurrencies()

    def parse_currency(self, currency):
        if not currency:
            raise PoloniexApiError(PoloniexErrorMessage.REQUIRED_PARAMETER_MISSING)

        if currency not in self.currencies:
            raise PoloniexApiError(PoloniexErrorMessage.INVALID_CURRENCY)

        return currency

    def parse_currency_pair(self, currency_pair):
        if not currency_pair:
            raise PoloniexApiError(PoloniexErrorMessage.REQUIRED_PARAMETER_MISSING)

        if currency_pair == 'all':
            return None

        if currency_pair not in self.tickers:
            raise PoloniexApiError(PoloniexErrorMessage.INVALID_CURRENCY_PAIR)

        return currency_pair
