from decimal import Decimal

from core.schema import OrderDirection


class BittrexParams:
    MIN_TRADE_TOTAL = Decimal('0.001')  # BTC
    TRADE_FEE_PCT = Decimal('0.0025')
    DECIMAL_SCALE = Decimal('0.00000001')


class BittrexErrorMessage:
    MARKET_NOT_PROVIDED = 'MARKET_NOT_PROVIDED'
    CURRENCY_NOT_PROVIDED = 'CURRENCY_NOT_PROVIDED'
    NONCE_NOT_PROVIDED = 'NONCE_NOT_PROVIDED'
    APIKEY_NOT_PROVIDED = 'APIKEY_NOT_PROVIDED'
    APISIGN_NOT_PROVIDED = 'APISIGN_NOT_PROVIDED'
    RATE_NOT_PROVIDED = 'RATE_NOT_PROVIDED'
    QUANTITY_NOT_PROVIDED = 'QUANTITY_NOT_PROVIDED'
    APIKEY_INVALID = 'APIKEY_INVALID'
    INVALID_SIGNATURE = 'INVALID_SIGNATURE'
    INVALID_MARKET = 'INVALID_MARKET'
    INVALID_CURRENCY = 'INVALID_CURRENCY'
    QUANTITY_INVALID = 'QUANTITY_INVALID'
    RATE_INVALID = 'RATE_INVALID'
    MIN_TRADE_REQUIREMENT_NOT_MET = 'MIN_TRADE_REQUIREMENT_NOT_MET'
    DUST_TRADE_DISALLOWED_MIN_VALUE_50K_SAT = 'DUST_TRADE_DISALLOWED_MIN_VALUE_50K_SAT'
    INSUFFICIENT_FUNDS = 'INSUFFICIENT_FUNDS'
    ORDER_NOT_OPEN = 'ORDER_NOT_OPEN'
    UUID_NOT_PROVIDED = 'UUID_NOT_PROVIDED'
    UUID_INVALID = 'UUID_INVALID'
    INVALID_ORDER = 'INVALID_ORDER'
    ADDRESS_GENERATING = 'ADDRESS_GENERATING'
    ADDRESS_NOT_PROVIDED = 'ADDRESS_NOT_PROVIDED'  # TODO: check
    ADDRESS_INVALID = 'ADDRESS_INVALID'  # TODO: check


class BittrexApiError(Exception):

    def __init__(self, message, *args):
        super(BittrexApiError, self).__init__(*args)
        self.message = message

    def get_response(self):
        return dict(
            success=False,
            message=self.message,
            result=None
        )


class BittrexOrderType:
    BUY_LIMIT = 'BUY_LIMIT'
    SELL_LIMIT = 'SELL_LIMIT'

    @staticmethod
    def from_direction(direction):
        mapping = {
            OrderDirection.BUY: BittrexOrderType.BUY_LIMIT,
            OrderDirection.SELL: BittrexOrderType.SELL_LIMIT
        }
        return mapping[direction]
