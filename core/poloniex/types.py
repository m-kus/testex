from decimal import Decimal


class PoloniexParams:
    MIN_TRADE_TOTAL = Decimal('0.0001')  # BTC
    TAKER_FEE_PCT = Decimal('0.002')
    MAKER_FEE_PCT = Decimal('0.001')
    DECIMAL_SCALE = Decimal('0.00000001')


class PoloniexOrderStatus:
    OPEN = 'Open'
    PARTIALLY_FILLED = 'Partially filled'


class PoloniexAccountType:
    EXCHANGE = 'exchange'


class PoloniexErrorMessage:
    INVALID_COMMAND = 'Invalid command.'
    INVALID_API_KEY_SECRET_PAIR = 'Invalid API key/secret pair.'
    INVALID_ACCOUNT = 'Invalid account parameter.'
    INVALID_CURRENCY = 'Invalid currency parameter.'
    INVALID_START = 'Invalid start parameter.'
    INVALID_END = 'Invalid end parameter.'
    INVALID_CURRENCY_PAIR = 'Invalid currencyPair parameter.'
    INVALID_RATE = 'Invalid rate parameter.'
    INVALID_AMOUNT = 'Invalid amount parameter.'
    INVALID_ADDRESS = 'Invalid address parameter.'
    REQUIRED_PARAMETER_MISSING = 'Required parameter missing.'
    TOTAL_TOO_SMALL = 'Total must be at least 0.0001.'
    NOT_ENOUGH_CURRENCY = 'Not enough {currency}.'
    INVALID_NONCE = 'Invalid nonce parameter.'
    NONCE_NOT_GREATER = 'Nonce must be greater than {prev_nonce}. You provided {nonce}.'
    INVALID_ORDER_NUMBER = 'Invalid orderNumber parameter.'
    ORDER_NOT_FOUND = 'Invalid order number, or you are not the person who placed the order.'


class PoloniexApiError(Exception):

    def __init__(self, message, *args):
        super(PoloniexApiError, self).__init__(*args)
        self.message = message

    def get_response(self):
        return dict(error=self.message)
