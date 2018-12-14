from parameterized import parameterized
from unittest.mock import patch, MagicMock
from core.helpers import sign_message
from urllib.parse import urlencode

from tests.test_case import FlaskTestCase


class ApiAuthTests(FlaskTestCase):

    def setUp(self):
        self.app.executor = MagicMock()
        self.app.executor.process.return_value = None

    @parameterized.expand([
        ('', {}, 'NONCE_NOT_PROVIDED'),
        ('?nonce=1', {}, 'APIKEY_NOT_PROVIDED'),
        ('?nonce=1&apikey=1', {}, 'APISIGN_NOT_PROVIDED'),
        ('?nonce=1&apikey=1', {'apisign': '1'}, 'INVALID_SIGNATURE'),
    ])
    @patch('core.bittrex.stub.BittrexApiStub.send_order')
    def test_bittrex_v11_api_auth_failed(self, query, headers, message, send_order):
        rv = self.client.get('/bittrex.com/api/v1.1/market/buylimit' + query, headers=headers)
        self.assertEqual(200, rv.status_code)
        res = dict(success=False, result=None, message=message)
        self.assertDictEqual(res, rv.json)
        self.assertFalse(send_order.called)

    @patch('core.bittrex.stub.BittrexApiStub.send_order')
    def test_bittrex_v11_api_auth_succeeded(self, send_order):
        self.client.get('/bittrex.com/api/v1.1/market/buylimit?nonce=1&apikey=1', headers={
            'apisign': sign_message(
                'http://localhost/bittrex.com/api/v1.1/market/buylimit?nonce=1&apikey=1',
                key='1'
            )
        })
        self.assertTrue(send_order.called)

    @parameterized.expand([
        ({}, {}, 'Invalid nonce parameter.'),
        ({'Key': '42'}, {}, 'Invalid nonce parameter.'),
        ({'Key': '42'}, {'nonce': '777'}, 'Invalid API key/secret pair.'),
    ])
    @patch('core.poloniex.stub.PoloniexApiStub.return_balances')
    def test_poloniex_api_auth_failed(self, headers, data, error, return_balances):
        rv = self.client.post('/poloniex.com/tradingApi', headers=headers, data=data)
        self.assertEqual(200, rv.status_code)
        res = dict(error=error)
        self.assertDictEqual(res, rv.json)
        self.assertFalse(return_balances.called)

    @patch('core.poloniex.stub.PoloniexApiStub.return_balances')
    def test_poloniex_api_auth_succeeded(self, return_balances):
        data = {
            'nonce': '777',
            'command': 'returnBalances'
        }
        headers = {
            'Key': '42',
            'Sign': sign_message(urlencode(data), key='42')
        }
        self.client.post('/poloniex.com/tradingApi', headers=headers, data=data)
        self.assertTrue(return_balances.called)
