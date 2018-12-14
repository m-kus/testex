import requests
import simplejson as json
from cachetools import TTLCache, cached
from urllib.parse import urljoin

from core.bittrex.types import BittrexApiError, BittrexErrorMessage
from core.helpers import obj_dropna


class BittrexRawRequest:
    base_url = 'https://bittrex.com/api/v1.1/public/'

    def get_response(self, response: requests.Response):
        return response

    def request(self, method, **params):
        res = requests.get(
            url=urljoin(self.base_url, method),
            headers={'content-Type': 'application/json'},
            params=obj_dropna(params)
        )
        return self.get_response(res)

    def __getattr__(self, item):
        def method(**kwargs):
            return self.request(method=item, **kwargs)

        return method


class BittrexJsonRequest(BittrexRawRequest):

    def get_response(self, response: requests.Response):
        if response.status_code in [200, 201]:
            data = json.loads(response.text, use_decimal=True)
            if not data['success']:
                raise BittrexApiError(data.get('message', ''))
        else:
            raise requests.HTTPError(response=response)

        return data.get('result')


class BittrexApiProxy:

    def __init__(self):
        self.raw = BittrexRawRequest()
        self.json = BittrexJsonRequest()

    @cached(TTLCache(ttl=3600, maxsize=128))
    def get_markets(self):
        return self.raw.getmarkets()

    @cached(TTLCache(ttl=3600, maxsize=128))
    def get_currencies(self):
        return self.raw.getcurrencies()

    @cached(TTLCache(ttl=5, maxsize=128))
    def get_ticker(self, market):
        return self.raw.getticker(market=market)

    @cached(TTLCache(ttl=60, maxsize=128))
    def get_market_summaries(self):
        return self.raw.getmarketsummaries()

    @cached(TTLCache(ttl=60, maxsize=128))
    def get_market_summary(self, market):
        return self.raw.getmarketsummary(market=market)

    @cached(TTLCache(ttl=5, maxsize=128))
    def get_order_book(self, market, _type='both'):
        return self.raw.getorderbook(market=market, type=_type)

    @cached(TTLCache(ttl=5, maxsize=128))
    def get_market_history(self, market):
        return self.raw.getmarkethistory(market=market)

    @property
    @cached(TTLCache(ttl=3600, maxsize=128))
    def currencies(self) -> dict:
        result = self.json.getcurrencies()
        return {
            item['Currency']: item
            for item in result
        }

    @property
    @cached(TTLCache(ttl=3600, maxsize=128))
    def markets(self) -> dict:
        result = self.json.getmarkets()
        return {
            item['MarketName']: item
            for item in result
        }

    def parse_market(self, market, optional=False):
        if not market:
            if optional:
                return market
            raise BittrexApiError(BittrexErrorMessage.MARKET_NOT_PROVIDED)

        if market not in self.markets:
            raise BittrexApiError(BittrexErrorMessage.INVALID_MARKET)

        return market

    def parse_currency(self, currency, optional=False):
        if not currency:
            if optional:
                return currency
            raise BittrexApiError(BittrexErrorMessage.CURRENCY_NOT_PROVIDED)

        if currency not in self.currencies:
            raise BittrexApiError(BittrexErrorMessage.INVALID_CURRENCY)

        return currency
