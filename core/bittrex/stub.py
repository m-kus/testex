from decimal import Decimal
from uuid import uuid4

from core.helpers import sign_message, make_response
from core.schema import Executor, OrderDirection, OrderStatus, TransactionType, CustomLogicMixin
from core.bittrex.proxy import BittrexApiProxy
from core.bittrex.types import BittrexApiError, BittrexErrorMessage, BittrexParams
from core.bittrex.formatters import parse_quantity, parse_rate, parse_uuid, parse_address, format_balance, \
    format_history_order, format_open_order, format_single_order, format_deposit, format_withdrawal


class BittrexApiStub(BittrexApiProxy, CustomLogicMixin):
    __exchange_id__ = 'bittrex'

    def __init__(self, executor=None, *args, **kwargs):
        super(BittrexApiStub, self).__init__(*args, **kwargs)
        self.api_key = kwargs.get('api_key')
        self.executor = None  # type: Executor
        if executor:
            self.init_executor(executor)

    def init_executor(self, executor):
        self.executor = executor
        self.executor.register_custom_logic(self)

    def switch_user(self, url, nonce, api_key, api_sign):
        if not nonce:
            raise BittrexApiError(BittrexErrorMessage.NONCE_NOT_PROVIDED)
        if not api_key:
            raise BittrexApiError(BittrexErrorMessage.APIKEY_NOT_PROVIDED)
        if not api_sign:
            raise BittrexApiError(BittrexErrorMessage.APISIGN_NOT_PROVIDED)

        api_secret = api_key   # TODO: check api key existence in the future and get secret and all other settings
        valid_sign = sign_message(url, api_secret)
        if valid_sign != api_sign:
            raise BittrexApiError(BittrexErrorMessage.INVALID_SIGNATURE)

        self.api_key = api_key

    def extend_order(self, order: dict) -> dict:
        order = order.copy()

        order['executed_amount'] = order.get('executed_amount', Decimal())
        order['total'] = (order['executed_amount'] * order.get('average_price', Decimal()))\
            .quantize(BittrexParams.DECIMAL_SCALE)
        order['fee'] = (order['total'] * BittrexParams.TRADE_FEE_PCT)\
            .quantize(BittrexParams.DECIMAL_SCALE)
        order['remaining_amount'] = order['amount'] - order['executed_amount']

        if order['direction'] == OrderDirection.BUY:
            order['reserved'] = (order['amount'] * order['price'])\
                .quantize(BittrexParams.DECIMAL_SCALE)
            order['reserved_fee'] = (order['reserved'] * BittrexParams.TRADE_FEE_PCT)\
                .quantize(BittrexParams.DECIMAL_SCALE)
        else:
            order['reserved'] = order['amount']
            order['reserved_fee'] = Decimal()

        return order

    def check_balance(self, amount: Decimal, currency):
        balance = self.get_balance(currency)
        if amount > balance.get('available', Decimal()):
            raise BittrexApiError(BittrexErrorMessage.INSUFFICIENT_FUNDS)

    def send_order(self, direction, market, quantity: Decimal, rate: Decimal):
        market = self.parse_market(market)
        quantity = parse_quantity(quantity)
        rate = parse_rate(rate)

        base_currency = self.markets[market]['BaseCurrency']
        market_currency = self.markets[market]['MarketCurrency']

        self.check_balance(quantity, base_currency if direction == OrderDirection.BUY else market_currency)

        min_trade_size = self.markets[market]['MinTradeSize']
        if quantity < min_trade_size:
            raise BittrexApiError(BittrexErrorMessage.MIN_TRADE_REQUIREMENT_NOT_MET)

        if quantity * rate < BittrexParams.MIN_TRADE_TOTAL:
            raise BittrexApiError(BittrexErrorMessage.DUST_TRADE_DISALLOWED_MIN_VALUE_50K_SAT)

        uuid = str(uuid4())
        # TODO: connection reset here (with prob)
        self.executor.send_order(
            api_key=self.api_key,
            exchange_id=self.__exchange_id__,
            number=uuid,
            direction=direction,
            amount=quantity,
            price=rate,
            market=market,
            base_currency=base_currency,
            market_currency=market_currency,
            fee_currency=base_currency
        )
        # TODO: and here (with prob too)
        return make_response(dict(uuid=uuid))

    def cancel(self, uuid):
        uuid = parse_uuid(uuid)
        order = self.executor.get_order(self.api_key, uuid)
        if not order:
            raise BittrexApiError(BittrexErrorMessage.INVALID_ORDER)

        if order['status'] != OrderStatus.OPENED:
            raise BittrexApiError(BittrexErrorMessage.ORDER_NOT_OPEN)

        self.executor.cancel_order(self.api_key, uuid)
        return make_response()

    def get_open_orders(self, market=None):
        market = self.parse_market(market, optional=True)
        orders = self.executor.get_orders(
            api_key=self.api_key,
            status=OrderStatus.OPENED,
            market=market
        )
        return make_response(list(map(
            lambda x: format_open_order(self.extend_order(x)),
            orders
        )))

    def get_balances(self):
        balances = self.executor.get_balances(self.api_key)
        return make_response(list(map(format_balance, balances)))

    def get_balance(self, currency):
        currency = self.parse_currency(currency)
        balance = self.executor.get_balance(self.api_key, currency)
        return make_response(format_balance(balance))

    def get_deposit_address(self, currency):
        self.parse_currency(currency)
        raise BittrexApiError(BittrexErrorMessage.ADDRESS_GENERATING)  # TODO: testnet wallet

    def withdraw(self, currency, quantity: Decimal, address, payment_id=None):
        currency = self.parse_currency(currency)
        quantity = parse_quantity(quantity)
        address = parse_address(address, currency)

        self.check_balance(quantity, currency)

        uuid = str(uuid4())
        self.executor.send_transaction(
            api_key=self.api_key,
            number=uuid,
            type=TransactionType.WITHDRAWAL,
            currency=currency,
            amount=quantity,
            address=address,
            fee=self.currencies[currency]['TxFee'],
            payment_id=payment_id
        )
        return make_response(dict(uuid=uuid))

    def get_order(self, uuid):
        uuid = parse_uuid(uuid)
        order = self.executor.get_order(
            api_key=self.api_key,
            number=uuid
        )
        if not order:
            raise BittrexApiError(BittrexErrorMessage.INVALID_ORDER)

        return make_response(format_single_order(self.extend_order(order)))

    def get_order_history(self, market=None):
        market = self.parse_market(market, optional=True)
        orders = self.executor.get_orders(
            api_key=self.api_key,
            status=OrderStatus.CLOSED,
            market=market
        )
        return make_response(list(map(
            lambda x: format_history_order(self.extend_order(x)),
            orders
        )))

    def get_transactions(self, _type, formatter, currency=None):
        currency = self.parse_currency(currency, optional=True)
        transactions = self.executor.get_transactions(
            api_key=self.api_key,
            _type=_type,
            currency=currency
        )
        return make_response(list(map(formatter, transactions)))

    def get_withdrawal_history(self, currency=None):
        return self.get_transactions(
            _type=TransactionType.WITHDRAWAL,
            currency=currency,
            formatter=format_withdrawal
        )

    def get_deposit_history(self, currency=None):
        return self.get_transactions(
            _type=TransactionType.DEPOSIT,
            currency=currency,
            formatter=format_deposit
        )
