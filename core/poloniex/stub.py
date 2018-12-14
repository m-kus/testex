from datetime import datetime
from itertools import groupby
from decimal import Decimal
from random import SystemRandom

from core.poloniex.proxy import PoloniexApiProxy
from core.poloniex.formatters import format_balance, parse_datetime, format_deposit, format_withdrawal, \
    format_order, parse_limit, format_trade, format_order_status, parse_decimal, parse_address, \
    split_currency_pair
from core.poloniex.types import PoloniexApiError, PoloniexErrorMessage, PoloniexParams, PoloniexAccountType
from core.schema import CustomLogicMixin, OrderDirection, Executor, TransactionType, OrderStatus, OrderType
from core.helpers import sign_message


class PoloniexApiStub(PoloniexApiProxy, CustomLogicMixin):
    __exchange_id__ = 'poloniex'

    def __init__(self, executor=None, *args, **kwargs):
        super(PoloniexApiStub, self).__init__(*args, **kwargs)
        self.api_key = kwargs.get('api_key')
        self.executor = None  # type: Executor
        self.rnd = SystemRandom(datetime.now().timestamp())
        self.nonces = dict()
        if executor:
            self.init_executor(executor)

    def get_number(self) -> int:
        return self.rnd.randint(1, 999999999)

    def parse_nonce(self, nonce):
        try:
            nonce = int(nonce)
        except TypeError:
            raise PoloniexApiError(PoloniexErrorMessage.INVALID_NONCE)

        prev_nonce = self.nonces.get(self.api_key, 0)
        if int(nonce) <= prev_nonce:
            raise PoloniexApiError(PoloniexErrorMessage.NONCE_NOT_GREATER.format(
                prev_nonce=prev_nonce, nonce=nonce))

        self.nonces[self.api_key] = nonce

    def switch_user(self, api_key, api_sign, nonce, data):
        self.parse_nonce(nonce)

        api_secret = api_key
        if any([not api_key, not api_sign, sign_message(data, api_secret) != api_sign]):
            raise PoloniexApiError(PoloniexErrorMessage.INVALID_API_KEY_SECRET_PAIR)

        self.api_key = api_key

    def init_executor(self, executor):
        self.executor = executor
        self.executor.register_custom_logic(self)

    def extend_order(self, order: dict):
        order = order.copy()

        order['executed_amount'] = order.get('executed_amount', Decimal())
        order['total'] = (order['executed_amount'] * order.get('average_price', Decimal())) \
            .quantize(PoloniexParams.DECIMAL_SCALE)
        order['remaining_amount'] = order['amount'] - order['executed_amount']

        if order['direction'] == OrderDirection.BUY:
            order['reserved'] = (order['amount'] * order['price']) \
                .quantize(PoloniexParams.DECIMAL_SCALE)
            order['fee'] = (order['executed_amount'] * PoloniexParams.TAKER_FEE_PCT) \
                .quantize(PoloniexParams.DECIMAL_SCALE)
        else:
            order['reserved'] = order['amount']
            order['fee'] = (order['total'] * PoloniexParams.TAKER_FEE_PCT) \
                .quantize(PoloniexParams.DECIMAL_SCALE)

        order['reserved_fee'] = Decimal()
        return order

    def check_balance(self, amount: Decimal, currency):
        balance = self.executor.get_balance(api_key=self.api_key, currency=currency)
        if amount > balance.get('available', Decimal()):
            raise PoloniexApiError(PoloniexErrorMessage.NOT_ENOUGH_CURRENCY.format(currency=currency))

    def return_balances(self):
        result = {
            currency: Decimal()
            for currency in self.currencies
        }

        balances = self.executor.get_balances(self.api_key)
        for item in balances:
            result[item['currency']] = item.get('available', Decimal())

        return result

    def return_complete_balances(self, account):
        if account and account != PoloniexAccountType.EXCHANGE:  # TODO: implement others
            raise PoloniexApiError(PoloniexErrorMessage.INVALID_ACCOUNT)

        balances = self.executor.get_balances(self.api_key)
        return {
            item['currency']: format_balance(item, self.tickers)
            for item in balances
        }

    def return_deposit_addresses(self):
        return dict()

    def generate_new_address(self, currency):
        currency = self.parse_currency(currency)
        return dict(
            success=0,
            response=None  # TODO: implement
        )

    def return_deposits_withdrawals(self, start, end):
        transactions = self.executor.get_transactions(
            api_key=self.api_key,
            start_at=parse_datetime(start, PoloniexErrorMessage.INVALID_START),
            end_at=parse_datetime(end, PoloniexErrorMessage.INVALID_END)
        )

        deposits = filter(lambda x: x['type'] == TransactionType.DEPOSIT, transactions)
        withdrawals = filter(lambda x: x['type'] == TransactionType.WITHDRAWAL, transactions)

        return dict(
            deposits=list(map(format_deposit, deposits)),
            withdrawals=list(map(format_withdrawal, withdrawals))
        )

    def return_open_orders(self, currency_pair):
        currency_pair = self.parse_currency_pair(currency_pair)
        orders = self.executor.get_orders(
            api_key=self.api_key,
            status=OrderStatus.OPENED,
            market=currency_pair
        )

        if currency_pair:
            return list(map(format_order, orders))

        return {
            market: list(map(format_order, g))
            for market, g in groupby(orders, key=lambda x: x['market'])
        }

    def return_account_trade_history(self, currency_pair, start, end, limit):
        currency_pair = self.parse_currency_pair(currency_pair)
        trades = self.executor.get_trades(
            api_key=self.api_key,
            limit=parse_limit(limit),
            market=currency_pair,
            start_at=parse_datetime(start, PoloniexErrorMessage.INVALID_START),
            end_at=parse_datetime(end, PoloniexErrorMessage.INVALID_END)
        )

        if currency_pair:
            return list(map(format_trade, trades))

        return {
            market: list(map(format_trade, g))
            for market, g in groupby(trades, key=lambda x: x['market'])
        }

    def return_order_trades(self, order_number):
        trades = self.executor.get_trades(
            api_key=self.api_key,
            order_number=order_number
        )
        return list(map(format_trade, trades))

    def get_order(self, order_number):
        if not order_number:
            raise PoloniexApiError(PoloniexErrorMessage.REQUIRED_PARAMETER_MISSING)

        try:
            order_number = int(order_number)
        except TypeError:
            raise PoloniexApiError(PoloniexErrorMessage.INVALID_ORDER_NUMBER)

        order = self.executor.get_order(self.api_key, order_number)
        if not order:
            raise PoloniexApiError(PoloniexErrorMessage.ORDER_NOT_FOUND)

        return order

    def return_order_status(self, order_number):
        order = self.get_order(order_number)
        if order['status'] == OrderStatus.OPENED:
            return dict(
                result={order_number: format_order_status(order)},
                success=1
            )
        return dict(success=0)

    def send_order(self, direction, currency_pair, rate, amount,
                   fill_or_kill=None, immediate_or_cancel=None, post_only=None):
        number = self.get_number()
        price = parse_decimal(rate, PoloniexErrorMessage.INVALID_RATE)
        amount = parse_decimal(amount, PoloniexErrorMessage.INVALID_AMOUNT)
        market = self.parse_currency_pair(currency_pair)

        if price * amount < PoloniexParams.MIN_TRADE_TOTAL:
            raise PoloniexApiError(PoloniexErrorMessage.TOTAL_TOO_SMALL)

        base_currency, market_currency = split_currency_pair(market)
        self.check_balance(amount, base_currency if direction == OrderDirection.BUY else market_currency)

        self.executor.send_order(
            api_key=self.api_key,
            exchange_id=self.__exchange_id__,
            number=number,
            direction=direction,
            market=market,
            price=price,
            amount=amount,
            type=OrderType.init(fill_or_kill, immediate_or_cancel, post_only),
            base_currency=base_currency,
            market_currency=market_currency,
            fee_currency=base_currency if direction == OrderDirection.SELL else market_currency
        )
        return dict(
            orderNumber=number,
            resultingTrades=None  # TODO: implement
        )

    def cancel_order(self, order_number):
        order = self.get_order(order_number)
        if order['status'] != OrderStatus.OPENED:
            raise PoloniexApiError(PoloniexErrorMessage.ORDER_NOT_FOUND)

        order = self.executor.cancel_order(self.api_key, order_number)
        return dict(
            amount=order['remaining_amount'],
            message='Order #{} canceled.'.format(order_number),
            success=1
        )

    def move_order(self, order_number, rate, amount=None,
                   immediate_or_cancel=None, post_only=None):
        raise NotImplementedError  # TODO: implement

    def withdraw(self, currency, amount, address, payment_id=None):
        currency = self.parse_currency(currency)
        amount = parse_decimal(amount, PoloniexErrorMessage.INVALID_AMOUNT)
        self.check_balance(amount, currency)

        self.executor.send_transaction(
            api_key=self.api_key,
            exchange_id=self.__exchange_id__,
            number=self.get_number(),
            type=TransactionType.WITHDRAWAL,
            currency=currency,
            amount=amount,
            address=parse_address(address, currency),
            payment_id=payment_id
        )
        return dict(response='Withdrew {} {}.'.format(amount, currency))

    @staticmethod
    def return_fee_info(self):
        return dict(
            makerFee=PoloniexParams.MAKER_FEE_PCT,
            takerFee=PoloniexParams.TAKER_FEE_PCT,
            thirtyDayVolume=Decimal(),
            nextTier=Decimal()
        )

    def return_available_account_balances(self, account=None):
        if account:
            if account != 'exchange':
                raise NotImplementedError
            return self.return_balances()
        return dict(exchange=self.return_balances())
