from parameterized import parameterized
from unittest.mock import patch, MagicMock, PropertyMock
from decimal import Decimal

from tests.test_case import FlaskTestCase

MARKETS = {
    'BTC-XRP': {
        'BaseCurrency': 'BTC',
        'MarketCurrency': 'XRP',
        'MinTradeSize': Decimal('100')
    }
}


class BittrexMarketTests(FlaskTestCase):

    def setUp(self):
        self.app.executor = MagicMock()
        self.app.executor.process.return_value = None

    @parameterized.expand([
        ('', 'MARKET_NOT_PROVIDED'),
        ('?market=AZAZA', 'INVALID_MARKET'),
        ('?market=BTC-XRP', 'QUANTITY_NOT_PROVIDED'),
        ('?market=BTC-XRP&quantity=azaza', 'QUANTITY_INVALID'),
        ('?market=BTC-XRP&quantity=1', 'RATE_NOT_PROVIDED'),
        ('?market=BTC-XRP&quantity=1&rate=azaza', 'RATE_INVALID'),
        ('?market=BTC-XRP&quantity=1&rate=0.000001', 'MIN_TRADE_REQUIREMENT_NOT_MET'),
        ('?market=BTC-XRP&quantity=100&rate=0.000001', 'DUST_TRADE_DISALLOWED_MIN_VALUE_50K_SAT'),
    ])
    @patch('core.bittrex.stub.BittrexApiStub.check_balance')
    @patch('core.bittrex.stub.BittrexApiStub.switch_user')
    @patch('core.bittrex.stub.BittrexApiStub.markets', new_callable=PropertyMock, return_value=MARKETS)
    def test_bittrex_market_v11_buylimit_failed(self, query, message,
                                                _markets, _switch_user, _check_balance):
        rv = self.client.get('/bittrex.com/api/v1.1/market/buylimit' + query)
        self.assertEqual(200, rv.status_code)
        res = dict(result=None, success=False, message=message)
        self.assertDictEqual(res, rv.json)

    @parameterized.expand([
        ('/bittrex.com/api/v1.1/market/buylimit?market=BTC-XRP&quantity=200&rate=0.00001',),
        ('/bittrex.com/api/v1.1/market/selllimit?market=BTC-XRP&quantity=200&rate=0.00001',),
    ])
    @patch('core.executor.SimpleExecutor.send_order')
    @patch('core.bittrex.stub.uuid4', return_value='123')
    @patch('core.bittrex.stub.BittrexApiStub.check_balance')
    @patch('core.bittrex.stub.BittrexApiStub.switch_user')
    @patch('core.bittrex.stub.BittrexApiStub.markets', new_callable=PropertyMock, return_value=MARKETS)
    def test_bittrex_market_v11_limit_succeeded(self, url, _markets, _switch_user, _check_balance,
                                                _uuid4, send_order):
        rv = self.client.get(url)
        self.assertEqual(200, rv.status_code)
        res = dict(result=dict(uuid='123'), success=True, message='')
        self.assertDictEqual(res, rv.json)
        self.assertTrue(send_order.called)
