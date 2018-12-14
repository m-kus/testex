from typing import List


class OrderDirection:
    BUY = 'buy'
    SELL = 'sell'

    @staticmethod
    def get_sign(direction):
        if direction == OrderDirection.BUY:
            return 1
        if direction == OrderDirection.SELL:
            return -1
        raise NotImplementedError


class OrderType:
    FOK = 'fill_or_kill'
    IOC = 'immediate_or_cancel'
    POST = 'post_only'
    LIMIT = 'limit'

    @staticmethod
    def init(fill_or_kill=None, immediate_or_cancel=None, post_only=None):
        if fill_or_kill:
            return OrderType.FOK
        if immediate_or_cancel:
            return OrderType.IOC
        if post_only:
            return OrderType.POST
        return OrderType.LIMIT


class OrderStatus:
    OPENED = 'opened'
    CLOSED = 'closed'


class TransactionType:
    DEPOSIT = 'deposit'
    WITHDRAWAL = 'withdrawal'

    @staticmethod
    def get_sign(_type):
        if _type == TransactionType.DEPOSIT:
            return 1
        if _type == TransactionType.WITHDRAWAL:
            return -1
        raise NotImplementedError


class TransactionStatus:
    NON_AUTHORIZED = 'non_authorized'
    CANCELED = 'canceled'
    PENDING = 'pending'
    CONFIRMED = 'confirmed'


class CustomLogicMixin:
    __exchange_id__ = None

    def extend_order(self, order: dict):
        raise NotImplementedError


class Executor:

    def register_custom_logic(self, custom_logic: CustomLogicMixin):
        raise NotImplementedError

    def send_order(self, api_key, number, **kwargs):
        raise NotImplementedError

    def get_order(self, api_key, number) -> dict:
        raise NotImplementedError

    def cancel_order(self, api_key, number):
        raise NotImplementedError

    def get_orders(self, api_key, status, market=None) -> List[dict]:
        raise NotImplementedError

    def send_transaction(self, api_key, number, **kwargs):
        raise NotImplementedError

    def get_transactions(self, api_key, _type=None, currency=None,
                         start_at=None, end_at=None) -> List[dict]:
        raise NotImplementedError

    def get_trades(self, api_key, order_number=None, market=None, limit=None,
                   start_at=None, end_at=None) -> List[dict]:
        raise NotImplementedError

    def get_balances(self, api_key) -> List[dict]:
        raise NotImplementedError

    def get_balance(self, api_key, currency=None) -> dict:
        raise NotImplementedError
