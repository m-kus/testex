from parameterized import parameterized
from unittest.mock import patch
from urllib.parse import parse_qsl, urlsplit, ParseResult

from tests.test_case import FlaskTestCase


class PublicEndpointsTests(FlaskTestCase):

    def assert_url_equal(self, route, call_args: dict):
        split_route = urlsplit('https:/' + route)  # type: ParseResult

        params = dict(parse_qsl(split_route.query))
        self.assertDictEqual(params, call_args['params'])

        url = split_route._replace(query=None).geturl()
        self.assertEqual(url, call_args['url'])

    @parameterized.expand([
        ('/bittrex.com/api/v1.1/public/getmarkets',),
        ('/bittrex.com/api/v1.1/public/getcurrencies',),
        ('/bittrex.com/api/v1.1/public/getticker?market=m',),
        ('/bittrex.com/api/v1.1/public/getmarketsummaries',),
        ('/bittrex.com/api/v1.1/public/getorderbook?market=m&type=t',),
        ('/bittrex.com/api/v1.1/public/getmarketsummary?market=m',),
        ('/bittrex.com/api/v1.1/public/getmarkethistory?market=m',),
        ('/poloniex.com/public?command=returnTicker',),
        ('/poloniex.com/public?command=return24hVolume',),
        ('/poloniex.com/public?command=returnOrderBook&currencyPair=c&depth=d',),
        ('/poloniex.com/public?command=returnTradeHistory&currencyPair=c&start=s&end=e',),
        ('/poloniex.com/public?command=returnChartData&currencyPair=c&start=s&end=e&period=p',),
        ('/poloniex.com/public?command=returnCurrencies',),
        ('/poloniex.com/public?command=returnLoanOrders&currency=c',),
    ])
    @patch('requests.get')
    def test_public(self, url, get):
        get.return_value = dict()

        rv = self.client.get(url)
        self.assertEqual(200, rv.status_code)

        self.assertEqual(1, get.call_count, msg='get not called')
        self.assert_url_equal(url, get.call_args[1])

        self.client.get(url)
        self.assertEqual(1, get.call_count, msg='cache not working')
