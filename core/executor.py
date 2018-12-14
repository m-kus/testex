import logging
from tabulate import tabulate
from uuid import uuid4
from pymongo.database import Database
from pymongo import ReturnDocument
from typing import List
from random import SystemRandom
from decimal import Decimal
from bson import Decimal128
from datetime import datetime
from collections import defaultdict
from typing import Dict

from core.helpers import obj_dec128_to_dec, obj_dec_to_dec128, obj_list_dec128_to_dec, obj_dropna, \
    make_mongo_interval_cond, mongo_auto_reconnect
from core.schema import Executor, OrderDirection, OrderStatus, TransactionType, TransactionStatus, \
    CustomLogicMixin

logger = logging.getLogger('testex')


class SimpleExecutorParams:
    NON_EXECUTE_PROB = .3


class SimpleExecutor(Executor):

    def __init__(self, db=None):
        self.rnd = SystemRandom()
        self.db = None  # type: Database
        self.custom_logic = dict()  # type: Dict[str, CustomLogicMixin]
        if db:
            self.init_db(db)

    def init_db(self, db: Database):
        self.db = db

    def register_custom_logic(self, custom_logic: CustomLogicMixin):
        self.custom_logic[custom_logic.__exchange_id__] = custom_logic

    def extend_order(self, order: dict) -> dict:
        if order.get('exchange_id') in self.custom_logic:
            return self.custom_logic[order['exchange_id']].extend_order(order)
        return order

    def make_trade(self, order: dict, amount=None) -> dict:
        if not amount:
            amount = min(
                order['remaining_amount'],
                Decimal(self.rnd.expovariate(1 / float(order['remaining_amount'])))
            )

        trade = dict(
            _id=str(uuid4()),
            api_key=order['api_key'],
            order_number=order['_id'],
            direction=order['direction'],
            price=order['price'],
            created_at=datetime.utcnow(),
            amount=amount
        )
        return trade

    def execute_order(self, order: dict,
                      non_execute_prob=SimpleExecutorParams.NON_EXECUTE_PROB,
                      trade_amount=None):

        if self.rnd.uniform(0, 1) < non_execute_prob:
            logger.debug('execute_order: skip execution')
            return

        order = self.extend_order(order)
        trade = self.make_trade(order, amount=trade_amount)
        average_price = (trade['amount'] * trade['price'] + order['total']) \
            / (trade['amount'] + order['executed_amount'])

        if trade['amount'] == order['remaining_amount']:
            status = OrderStatus.CLOSED
        else:
            status = OrderStatus.OPENED

        self.db.trades.insert_one(obj_dec_to_dec128(trade))
        order = self.db.orders.find_one_and_update(
            filter=dict(_id=order['_id']),
            update={
                "$inc": dict(
                    executed_amount=Decimal128(trade['amount'])
                ),
                "$set": dict(
                    average_price=Decimal128(average_price),
                    updated_at=trade['created_at'],
                    status=status
                )
            },
            return_document=ReturnDocument.AFTER
        )

        order = self.extend_order(obj_dec128_to_dec(order))
        if status == OrderStatus.CLOSED:
            self.on_order_closed(order)

        logger.info('execute_order: {} {} (of {}) {} at {} {}'.format(
            trade['direction'], trade['amount'], order['amount'], order['market_currency'],
            trade['price'], order['base_currency']))
        return order

    def sync_transaction(self, transaction: dict):
        transaction = self.db.transactions.find_one_and_update(
            filter=dict(
                _id=transaction['_id'],
                api_key=transaction['api_key']
            ),
            update={
                '$set': dict(
                    status=TransactionStatus.CONFIRMED,
                    updated_at=datetime.utcnow()
                )
            },
            return_document=ReturnDocument.AFTER
        )
        self.on_transaction_confirmed(obj_dec128_to_dec(transaction))

    def sync_transactions(self):
        transactions = self.db.transactions.find(dict(
            status={'$ne': TransactionStatus.CONFIRMED}
        ))
        for transaction in transactions:
            self.sync_transaction(transaction)

    def execute_orders(self):
        orders = self.db.orders.find(dict(status=OrderStatus.OPENED))
        for order in orders:
            self.execute_order(obj_dec128_to_dec(order))

    @mongo_auto_reconnect
    def process(self):
        self.execute_orders()
        self.sync_transactions()

    @mongo_auto_reconnect
    def send_order(self, api_key, number, **kwargs):
        order = dict(
            _id=number,
            api_key=api_key,
            status=OrderStatus.OPENED,
            created_at=datetime.utcnow()
        )
        order.update(**kwargs)
        self.db.orders.insert_one(obj_dec_to_dec128(order))

        order_ex = self.extend_order(order)
        self.on_order_opened(self.extend_order(order_ex))

        logger.info('send_order: {} {} {} at {} {}'.format(
            order['direction'], order['amount'], order['market_currency'],
            order['price'], order['base_currency']))
        return order_ex

    @mongo_auto_reconnect
    def send_transaction(self, api_key, number, **kwargs):
        transaction = dict(
            _id=number,
            api_key=api_key,
            status=TransactionStatus.NON_AUTHORIZED,
            created_at=datetime.utcnow()
        )
        transaction.update(**kwargs)

        self.db.transactions.insert_one(obj_dec_to_dec128(transaction))
        self.on_transaction_submitted(transaction)

        logger.info('send_transaction: {} {} {} -> {}'.format(
            transaction['type'], transaction['amount'], transaction['currency'],
            transaction['address']))
        return transaction

    @mongo_auto_reconnect
    def get_order(self, api_key, number):
        order = self.db.orders.find_one(dict(
            _id=number,
            api_key=api_key
        ))
        if order:
            return self.extend_order(obj_dec128_to_dec(order))

    @mongo_auto_reconnect
    def cancel_order(self, api_key, number):
        order = self.db.orders.find_one_and_update(
            filter=dict(
                _id=number,
                api_key=api_key
            ),
            update={
                "$set": dict(
                    status=OrderStatus.CLOSED,
                    updated_at=datetime.utcnow()
                )
            },
            return_document=ReturnDocument.AFTER
        )
        if order:
            order_ex = self.extend_order(obj_dec128_to_dec(order))
            self.on_order_closed(order_ex)
            logger.info('cancel_order: {} {} of {} {}'.format(
                order_ex['direction'], order_ex['executed_amount'],
                order_ex['amount'], order_ex['market_currency']))
            return order

    @mongo_auto_reconnect
    def get_orders(self, api_key, status, market=None):
        query = dict(
            api_key=api_key,
            status=status,
            market=market
        )
        orders = self.db.orders.find(obj_dropna(query))
        return list(map(self.extend_order, obj_list_dec128_to_dec(orders)))

    @mongo_auto_reconnect
    def get_transactions(self, api_key, _type=None, currency=None,
                         start_at=None, end_at=None) -> List[dict]:
        query = {'$and': [
            obj_dropna(dict(
                api_key=api_key,
                type=_type,
                currency=currency
            )),
            *make_mongo_interval_cond('created_at', start_at, end_at)
        ]}
        transactions = self.db.transactions.find(query)
        return obj_list_dec128_to_dec(transactions)

    @mongo_auto_reconnect
    def get_trades(self, api_key, order_number=None, market=None, limit=None,
                   start_at=None, end_at=None) -> List[dict]:
        query = {'$and': [
            obj_dropna(dict(
                api_key=api_key,
                market=market,
                order_number=order_number
            )),
            *make_mongo_interval_cond('created_at', start_at, end_at)
        ]}
        trades = self.db.trades.find(query)
        if limit:
            trades = trades.limit(limit)
        return obj_list_dec128_to_dec(trades)

    @mongo_auto_reconnect
    def get_balances(self, api_key):
        balances = self.db.balances.find(dict(api_key=api_key))
        return obj_list_dec128_to_dec(balances)

    @mongo_auto_reconnect
    def get_balance(self, api_key, currency=None):
        balance = self.db.balances.find_one(dict(
            api_key=api_key,
            currency=currency
        ))
        if not balance:
            balance = dict(
                api_key=api_key,
                currency=currency,
                available=Decimal()
            )

        return obj_dec128_to_dec(balance)

    @mongo_auto_reconnect
    def increment_balances(self, api_key, increments: dict):
        for currency, balance in increments.items():
            query = dict(
                api_key=api_key,
                currency=currency
            )
            data = obj_dec_to_dec128(balance)
            result = self.db.balances.update_one(query, update={'$inc': data})
            if result.matched_count == 0:
                self.db.balances.insert_one({
                    '_id': str(uuid4()),
                    **query,
                    **data
                })

        logger.debug('increment_balances:\n{}'.format(tabulate(increments)))

    def on_order_closed(self, order: dict):
        increments = defaultdict(lambda: defaultdict(Decimal))

        if order['direction'] == OrderDirection.BUY:
            increments[order['base_currency']]['frozen'] = -order['reserved']
            increments[order['base_currency']]['available'] = order['reserved'] - order['total']
            increments[order['market_currency']]['available'] = order['executed_amount']
        else:
            increments[order['market_currency']]['frozen'] = -order['reserved']
            increments[order['market_currency']]['available'] = order['reserved'] - order['executed_amount']
            increments[order['base_currency']]['available'] = order['total']

        increments[order['fee_currency']]['frozen'] -= order['reserved_fee']
        increments[order['fee_currency']]['available'] += order['reserved_fee'] - order['fee']
        self.increment_balances(order['api_key'], increments)

    def on_order_opened(self, order: dict):
        increments = defaultdict(lambda: defaultdict(Decimal))

        if order['direction'] == OrderDirection.BUY:
            increments[order['base_currency']]['frozen'] = order['reserved']
            increments[order['base_currency']]['available'] = -order['reserved']
        else:
            increments[order['market_currency']]['frozen'] = order['reserved']
            increments[order['market_currency']]['available'] = -order['reserved']

        increments[order['fee_currency']]['frozen'] += order['reserved_fee']
        increments[order['fee_currency']]['available'] -= order['reserved_fee']
        self.increment_balances(order['api_key'], increments)

    def on_transaction_submitted(self, transaction: dict):
        increments = defaultdict(lambda: defaultdict(Decimal))

        if transaction['type'] == TransactionType.WITHDRAWAL:
            increments[transaction['currency']]['available'] = -transaction['amount']
            key = 'frozen'
        else:
            key = 'pending'

        increments[transaction['currency']][key] = transaction['amount']
        self.increment_balances(transaction['api_key'], increments)

    def on_transaction_confirmed(self, transaction: dict):
        increments = defaultdict(lambda: defaultdict(Decimal))

        if transaction['type'] == TransactionType.WITHDRAWAL:
            key = 'frozen'
        else:
            key = 'pending'
            increments[transaction['currency']]['available'] = transaction['amount']

        increments[transaction['currency']][key] = -transaction['amount']
        self.increment_balances(transaction['api_key'], increments)

    def deposit(self, api_key, currency, quantity: Decimal):
        transaction = self.send_transaction(
            api_key=api_key,
            number=str(uuid4()),
            type=TransactionType.DEPOSIT,
            currency=currency,
            amount=quantity,
            address=None,
            status=TransactionStatus.CONFIRMED,
            updated_at=datetime.utcnow(),
            fee=Decimal()
        )
        self.on_transaction_confirmed(transaction)
