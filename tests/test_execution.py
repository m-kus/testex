from unittest import TestCase
from decimal import Decimal
from unittest import TestCase
from mongomock import MongoClient

from core.bittrex.stub import BittrexApiStub
from core.executor import SimpleExecutor
from core.schema import OrderDirection
from tests.test_case import patch_decimal128


class ExecutionTests(TestCase):

    @classmethod
    def setUpClass(cls):
        patch_decimal128()
        cls.client = MongoClient()
        cls.db = cls.client.get_database('testex')
        cls.executor = SimpleExecutor(db=cls.db)

    def test_execute_order(self):
        stub = BittrexApiStub(executor=self.executor)
        order = self.executor.send_order(
            api_key='test_bittrex_execution',
            exchange_id='bittrex',
            number='5',
            direction=OrderDirection.BUY,
            market='BTC-XRP',
            price=Decimal('0.000001'),
            amount=Decimal('500'),
            base_currency='BTC',
            market_currency='XRP',
            fee_currency='BTC'
        )

        order = self.executor.execute_order(order, non_execute_prob=0, trade_amount=Decimal('100'))
        self.assertEqual(Decimal('100'), order['executed_amount'])
        self.assertEqual(Decimal('0.000001'), order['average_price'])

        trades = self.executor.get_trades(
            api_key='test_bittrex_execution',
            order_number='5'
        )
        self.assertEqual(1, len(trades))
