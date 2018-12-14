from parameterized import parameterized
from unittest import TestCase
from mongomock import MongoClient
from decimal import Decimal

from core.bittrex.stub import BittrexApiStub
from core.poloniex.stub import PoloniexApiStub
from core.executor import SimpleExecutor
from core.schema import OrderStatus, OrderDirection
from tests.test_case import patch_decimal128

BITTREX_BUY_ORDER = dict(
    api_key='test_bittrex_buy',
    exchange_id='bittrex',
    number='1',
    direction=OrderDirection.BUY,
    market='BTC-XRP',
    price=Decimal('0.000001'),
    amount=Decimal('500'),
    base_currency='BTC',
    market_currency='XRP',
    fee_currency='BTC'
)
POLONIEX_BUY_ORDER = dict(
    api_key='test_poloniex_buy',
    exchange_id='poloniex',
    number='2',
    direction=OrderDirection.BUY,
    market='BTC_XRP',
    price=Decimal('0.000001'),
    amount=Decimal('500'),
    base_currency='BTC',
    market_currency='XRP',
    fee_currency='XRP'
)
BITTREX_SELL_ORDER = dict(
    api_key='test_bittrex_sell',
    exchange_id='bittrex',
    number='3',
    direction=OrderDirection.SELL,
    market='BTC-XRP',
    price=Decimal('0.000001'),
    amount=Decimal('500'),
    base_currency='BTC',
    market_currency='XRP',
    fee_currency='BTC'
)
POLONIEX_SELL_ORDER = dict(
    api_key='test_poloniex_sell',
    exchange_id='poloniex',
    number='4',
    direction=OrderDirection.SELL,
    market='BTC_XRP',
    price=Decimal('0.000001'),
    amount=Decimal('500'),
    base_currency='BTC',
    market_currency='XRP',
    fee_currency='BTC'
)


class ExecutorTradingTests(TestCase):

    @classmethod
    def setUpClass(cls):
        patch_decimal128()
        cls.client = MongoClient()
        cls.db = cls.client.get_database('testex')
        cls.executor = SimpleExecutor(db=cls.db)

    @parameterized.expand([
        (BITTREX_BUY_ORDER, BittrexApiStub(), 'BTC', Decimal('0.00050125')),
        (POLONIEX_BUY_ORDER, PoloniexApiStub(), 'BTC', Decimal('0.0005')),
        (BITTREX_SELL_ORDER, BittrexApiStub(), 'XRP', Decimal('500')),
        (POLONIEX_SELL_ORDER, PoloniexApiStub(), 'XRP', Decimal('500'))
    ])
    def test_send_and_cancel(self, order_body, stub, currency, reserved):
        stub.init_executor(self.executor)
        self.executor.send_order(**order_body)

        order = self.executor.get_order(
            api_key=order_body['api_key'],
            number=order_body['number']
        )
        self.assertIsNotNone(order)
        self.assertEqual(OrderStatus.OPENED, order['status'])

        balance = self.executor.get_balance(
            api_key=order_body['api_key'],
            currency=currency
        )
        self.assertEqual(reserved, balance['frozen'])
        self.assertEqual(-reserved, balance['available'])

        order = self.executor.cancel_order(
            api_key=order_body['api_key'],
            number=order_body['number']
        )
        self.assertIsNotNone(order)
        self.assertEqual(OrderStatus.CLOSED, order['status'])

        balance = self.executor.get_balance(
            api_key=order_body['api_key'],
            currency=currency
        )
        self.assertEqual(Decimal(), balance['frozen'], msg='frozen')
        self.assertEqual(Decimal(), balance['available'], msg='available')

    def test_cancel_partially_filled(self):
        stub = BittrexApiStub(executor=self.executor)
        self.executor.send_order(
            api_key='test_bittrex_parital_fill',
            exchange_id='bittrex',
            number='5',
            direction=OrderDirection.BUY,
            market='BTC-XRP',
            price=Decimal('0.000001'),
            amount=Decimal('500'),
            executed_amount=Decimal('200'),
            average_price=Decimal('0.000001'),
            base_currency='BTC',
            market_currency='XRP',
            fee_currency='BTC'
        )

        order = self.executor.cancel_order(
            api_key='test_bittrex_parital_fill',
            number='5'
        )
        self.assertIsNotNone(order)
        self.assertEqual(OrderStatus.CLOSED, order['status'])

        btc_balance = self.executor.get_balance(
            api_key='test_bittrex_parital_fill',
            currency='BTC'
        )
        self.assertEqual(Decimal(), btc_balance['frozen'], msg='frozen')
        self.assertEqual(Decimal('-0.0002005'), btc_balance['available'], msg='available')

        xrp_balance = self.executor.get_balance(
            api_key='test_bittrex_parital_fill',
            currency='XRP'
        )
        self.assertEqual(Decimal('200'), xrp_balance['available'], msg='available')
