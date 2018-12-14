from parameterized import parameterized
from unittest import TestCase
from mongomock import MongoClient
from datetime import datetime
from bson import Decimal128
from decimal import Decimal

from core.executor import SimpleExecutor
from core.schema import TransactionType, OrderStatus


class ExecutorCollectionTests(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = MongoClient()
        cls.db = cls.client.get_database('testex')
        cls.executor = SimpleExecutor(db=cls.db)

        cls.db.transactions.insert_one({
            '_id': '1',
            'api_key': 'test',
            'type': TransactionType.WITHDRAWAL,
            'currency': 'BTC',
            'created_at': datetime(2018, 12, 1, 10, 10),
            'amount': Decimal128('100')
        })
        cls.db.orders.insert_one({
            '_id': '2',
            'api_key': 'test',
            'status': OrderStatus.OPENED,
            'market': 'BTC_XRP',
            'amount': Decimal128('100')
        })
        cls.db.trades.insert_many([{
            '_id': '3',
            'api_key': 'test',
            'order_number': '2',
            'market': 'BTC_XRP',
            'created_at': datetime(2018, 12, 1, 10, 11),
            'amount': Decimal128('50')
        }, {
            '_id': '4',
            'api_key': 'test',
            'order_number': '2',
            'market': 'BTC_XRP',
            'created_at': datetime(2018, 12, 1, 10, 12),
            'amount': Decimal128('50')
        }])
        cls.db.balances.insert({
            '_id': '5',
            'api_key': 'test',
            'currency': 'XRP',
            'available': Decimal128('100')
        })

    @parameterized.expand([
        ('qwerty', None, None, None, None, 0),
        ('test', 'deposit', None, None, None, 0),
        ('test', 'withdrawal', 'LTC', None, None, 0),
        ('test', 'withdrawal', 'BTC', datetime(2018, 12, 2), datetime(2018, 12, 3), 0),
        ('test', None, None, None, None, 1),
        ('test', 'withdrawal', None, None, None, 1),
        ('test', 'withdrawal', 'BTC', None, None, 1),
        ('test', 'withdrawal', 'BTC', datetime(2018, 12, 1), datetime(2018, 12, 2), 1),
    ])
    def test_get_transactions(self, api_key, _type, currency, start_at, end_at, expected):
        transactions = self.executor.get_transactions(
            api_key=api_key,
            _type=_type,
            currency=currency,
            start_at=start_at,
            end_at=end_at
        )
        self.assertEqual(expected, len(transactions))
        if transactions:
            self.assertTrue(isinstance(transactions[0]['amount'], Decimal))

    @parameterized.expand([
        ('qwerty', None, None, 0),
        ('test', 'closed', None, 0),
        ('test', 'opened', 'BTC_LTC', 0),
        ('test', None, None, 1),
        ('test', 'opened', None, 1),
        ('test', 'opened', 'BTC_XRP', 1),
    ])
    def test_get_orders(self, api_key, status, market, expected):
        orders = self.executor.get_orders(
            api_key=api_key,
            status=status,
            market=market
        )
        self.assertEqual(expected, len(orders))
        if orders:
            self.assertTrue(isinstance(orders[0]['amount'], Decimal))

    @parameterized.expand([
        ('test', '2', Decimal('100')),
        ('test', '42', None)
    ])
    def test_get_order(self, api_key, number, amount):
        order = self.executor.get_order(api_key=api_key, number=number )
        if amount:
            self.assertIsNotNone(order)
            self.assertEqual(amount, order['amount'])
        else:
            self.assertIsNone(order)

    @parameterized.expand([
        ('qwerty', None, None, None, None, None, 0),
        ('test', '1', None, None, None, None, 0),
        ('test', '2', 'BTC_LTC', None, None, None, 0),
        ('test', '2', 'BTC_XRP', 1, None, None, 1),
        ('test', '2', 'BTC_XRP', 2, datetime(2018, 12, 1, 10, 11), None, 1),
        ('test', '2', 'BTC_XRP', 2, datetime(2018, 12, 1), datetime(2018, 12, 1, 10, 12), 1),
        ('test', None, None, None, None, None, 2),
        ('test', '2', None, None, None, None, 2),
        ('test', '2', 'BTC_XRP', None, None, None, 2),
        ('test', '2', 'BTC_XRP', 2, None, None, 2),
        ('test', '2', 'BTC_XRP', 2, datetime(2018, 12, 1), None, 2),
        ('test', '2', 'BTC_XRP', 2, datetime(2018, 12, 1), datetime(2018, 12, 2), 2),
    ])
    def test_get_trades(self, api_key, order_number, market, limit, start_at, end_at, expected):
        trades = self.executor.get_trades(
            api_key=api_key,
            order_number=order_number,
            market=market,
            limit=limit,
            start_at=start_at,
            end_at=end_at
        )
        self.assertEqual(expected, len(trades))
        if trades:
            self.assertTrue(isinstance(trades[0]['amount'], Decimal))

    @parameterized.expand([
        ('test', 1),
        ('qwerty', 0)
    ])
    def test_get_balances(self, api_key, expected):
        balances = self.executor.get_balances(api_key=api_key)
        self.assertEqual(expected, len(balances))
        if balances:
            self.assertTrue(isinstance(balances[0]['available'], Decimal))

    @parameterized.expand([
        ('test', 'XRP', Decimal('100')),
        ('qwerty', 'LTC', Decimal())
    ])
    def test_get_balance(self, api_key, currency, available):
        balance = self.executor.get_balance(api_key=api_key, currency=currency)
        self.assertEqual(api_key, balance['api_key'])
        self.assertEqual(currency, balance['currency'])
        self.assertEqual(available, balance['available'])
