from decimal import Decimal, InvalidOperation
from uuid import UUID

from core.bittrex.types import BittrexApiError, BittrexErrorMessage, BittrexOrderType
from core.schema import OrderStatus, TransactionStatus
from core.helpers import is_address_valid


def parse_quantity(quantity):
    if not quantity:
        raise BittrexApiError(BittrexErrorMessage.QUANTITY_NOT_PROVIDED)

    try:
        quantity = Decimal(quantity)
    except InvalidOperation:
        raise BittrexApiError(BittrexErrorMessage.QUANTITY_INVALID)

    return quantity


def parse_rate(rate):
    if not rate:
        raise BittrexApiError(BittrexErrorMessage.RATE_NOT_PROVIDED)

    try:
        rate = Decimal(rate)
    except InvalidOperation:
        raise BittrexApiError(BittrexErrorMessage.RATE_INVALID)

    return rate


def parse_uuid(uuid):
    if not uuid:
        raise BittrexApiError(BittrexErrorMessage.UUID_NOT_PROVIDED)

    try:
        UUID(uuid)
    except ValueError:
        raise BittrexApiError(BittrexErrorMessage.UUID_INVALID)

    return uuid


def parse_address(address, currency):
    if not address:
        raise BittrexApiError(BittrexErrorMessage.ADDRESS_NOT_PROVIDED)

    if not is_address_valid(address, currency):
        raise BittrexApiError(BittrexErrorMessage.ADDRESS_INVALID)

    return address


def format_datetime(dt):
    return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]


def format_order(order: dict, exclude_fields=None) -> dict:
    is_closed = order['status'] == OrderStatus.CLOSED
    order_type = BittrexOrderType.from_direction(order['direction'])
    created_at = format_datetime(order['created_at'])

    result = {
        'AccountId': None,
        'CancelInitiated': False,
        'Closed': format_datetime(order['updated_at']) if is_closed else None,
        'Commission': order['fee'],
        'CommissionPaid': order['fee'],
        'CommissionReserveRemaining': max(Decimal(), order['reserved_fee'] - order['fee']),
        'CommissionReserved': order['reserved_fee'],
        'Condition': 'NONE',
        'ConditionTarget': None,
        'Exchange': order['market'],
        'ImmediateOrCancel': False,
        'IsConditional': False,
        'IsOpen': not is_closed,
        'Limit': order['price'],
        'Opened': created_at,
        'OrderType': order_type,
        'OrderUuid': order['_id'],
        'Price': order['price'],
        'PricePerUnit': order.get('average_price'),
        'Quantity': order['amount'],
        'QuantityRemaining': order['remaining_amount'],
        'ReserveRemaining': order['reserved'] - order['total'],
        'Reserved': order['reserved'],
        'Sentinel': None,  # TODO: what is it?
        'TimeStamp': created_at,
        'Type': order_type,
        'Uuid': None
    }

    if exclude_fields:
        for field in exclude_fields:
            result.pop(field)

    return result


def format_open_order(order: dict) -> dict:
    return format_order(order, exclude_fields=[
        'AccountId',
        'Commission',
        'CommissionReserveRemaining',
        'CommissionReserved',
        'IsOpen',
        'ReserveRemaining',
        'Reserved',
        'Sentinel',
        'TimeStamp',
        'Type'
    ])


def format_history_order(order: dict) -> dict:
    return format_order(order, exclude_fields=[
        'AccountId',
        'CancelInitiated',
        'CommissionPaid',
        'CommissionReserveRemaining',
        'CommissionReserved',
        'IsOpen',
        'Opened',
        'ReserveRemaining',
        'Reserved',
        'Sentinel',
        'Type',
        'Uuid'
    ])


def format_single_order(order: dict) -> dict:
    return format_order(order, exclude_fields=[
        'Commission',
        'OrderType',
        'TimeStamp',
        'Uuid'
    ])


def format_balance(balance: dict) -> dict:
    available = balance.get('available', Decimal())
    pending = balance.get('pending', Decimal())
    result = {
        "Currency": balance['currency'],
        "Balance": available + pending + balance.get('frozen', Decimal()),  # TODO: check if it's true
        "Available": available,
        "Pending": pending,
        "CryptoAddress": None
    }
    return result


def format_deposit(transaction: dict) -> dict:
    result = {
        'Amount': transaction['amount'],
        'Confirmations': transaction.get('confirmations', 0),
        'CryptoAddress': transaction['address'],
        'Currency': transaction['currency'],
        'Id': transaction['_id'],
        'LastUpdated': format_datetime(transaction.get('updated_at', transaction['created_at'])),
        'TxId': transaction.get('hash')
    }
    return result


def format_withdrawal(transaction: dict) -> dict:
    result = {
        'Address': transaction['address'],
        'Amount': transaction['amount'],
        'Authorized': transaction['status'] not in [
            TransactionStatus.NON_AUTHORIZED, TransactionStatus.CANCELED],
        'Canceled': transaction['status'] == TransactionStatus.CANCELED,
        'Currency': transaction['currency'],
        'InvalidAddress': False,
        'Opened': format_datetime(transaction['created_at']),
        'PaymentUuid': transaction['_id'],
        'PendingPayment': transaction['status'] == TransactionStatus.PENDING,
        'TxCost': transaction['fee'],
        'TxId': transaction.get('hash')
    }
    return result
