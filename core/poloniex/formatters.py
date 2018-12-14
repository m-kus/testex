from decimal import Decimal, InvalidOperation
from datetime import datetime
from uuid import UUID

from core.poloniex.types import PoloniexParams, PoloniexApiError, PoloniexErrorMessage, PoloniexOrderStatus
from core.schema import TransactionStatus
from core.helpers import is_address_valid


def get_btc_market(currency):
    return 'BTC_{}'.format(currency)


def split_currency_pair(currency_pair: str) -> (str, str):
    return currency_pair.split('_', maxsplit=2)


def parse_datetime(timestamp, message='') -> datetime:
    try:
        dt = datetime.utcfromtimestamp(int(timestamp))
    except (ValueError, TypeError):
        raise PoloniexApiError(message)

    return dt


def parse_limit(limit) -> int:
    try:
        limit = int(limit)
        if limit < 0 or limit > 10000:
            raise ValueError
    except (ValueError, TypeError):
        limit = 500

    return limit


def parse_decimal(value, message) -> Decimal:
    if not value:
        raise PoloniexApiError(PoloniexErrorMessage.REQUIRED_PARAMETER_MISSING)

    try:
        value = Decimal(value)
    except InvalidOperation:
        raise PoloniexApiError(message)

    return value


def parse_address(address, currency):
    if not address:
        raise PoloniexApiError(PoloniexErrorMessage.REQUIRED_PARAMETER_MISSING)

    if not is_address_valid(address, currency):
        raise PoloniexApiError(PoloniexErrorMessage.INVALID_ADDRESS)

    return address


def format_timestamp(dt: datetime) -> int:
    return int(dt.timestamp())


def format_datetime(dt: datetime):
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def format_balance(balance: dict, tickers: dict) -> dict:
    market = get_btc_market(balance['currency'])
    available = balance.get('available', Decimal())
    frozen = balance.get('frozen', Decimal())
    result = {
        'available': available,
        'onOrders': frozen,
        'btcValue': ((available + frozen) * tickers[market]['last']).quantize(
            PoloniexParams.DECIMAL_SCALE)
    }
    return result


def format_deposit(transaction: dict) -> dict:
    if transaction['status'] == TransactionStatus.CONFIRMED:
        status = 'COMPLETE'
    else:
        status = ''  # TODO: determine

    result = {
      'currency': transaction['currency'],
      'address': transaction['address'],
      'amount': transaction['amount'],
      'confirmations': transaction.get('confirmations', 0),
      'txid': transaction.get('hash'),
      'timestamp': format_timestamp(transaction['created_at']),
      'status': status
    }
    return result


def format_withdrawal(transaction: dict) -> dict:
    if transaction['status'] == TransactionStatus.CONFIRMED:
        status = 'COMPLETE: {}'.format(transaction.get('hash'))
    else:
        status = ''  # TODO: determine

    result = {
      'withdrawalNumber': transaction['_id'],
      'currency': transaction['currency'],
      'address': transaction['address'],
      'amount': transaction['amount'],
      'timestamp': format_timestamp(transaction['created_at']),
      'status': status,
      'ipAddress': None  # TODO: from request?
    }
    return result


def format_order(order: dict) -> dict:
    result = {
        'orderNumber': order['_id'],
        'type': order['direction'],
        'rate': order['price'],
        'amount': order['amount'],
        'total': order['total']
    }
    return result


# Open orders only
def format_order_status(order: dict) -> dict:
    if order.get('executed_amount'):
        status = PoloniexOrderStatus.PARTIALLY_FILLED
    else:
        status = PoloniexOrderStatus.OPEN

    result = {
        'status': status,
        'rate': order['price'],
        'amount': order['amount'],
        'currencyPair': order['market'],
        'date': format_datetime(order['created_at']),
        'total': order['total'],
        'type': order['direction'],
        'startingAmount': order['remaining_amount']
    }
    return result


def format_trade(trade: dict) -> dict:
    trade_id = UUID(trade['_id']).int
    result = {
        'globalTradeID': trade_id % 4294967296,
        'tradeID': trade_id % 1048576,
        'date': format_datetime(trade['created_at']),
        'rate': trade['price'],
        'amount': trade['amount'],
        'total': (trade['price'] * trade['amount']).quantize(PoloniexParams.DECIMAL_SCALE),
        'fee': PoloniexParams.TAKER_FEE_PCT,
        'orderNumber': trade['order_number'],
        'type': trade['direction'],
        'category': 'exchange'
    }
    return result
