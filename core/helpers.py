import codecs
import hashlib
import hmac
import logging
import time
import requests
import simplejson as json
from functools import wraps
from pymongo.errors import AutoReconnect
from typing import List
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from decimal import Decimal
from bson import Decimal128
from hashlib import sha256


address_prefixes = {
    'BTC':   ['00', '05'],
    'TBTC':  ['6f', 'c4'],
    'BCH':   ['00', '05'],
    'TBCH':  ['6f', 'c4'],
    'LTC':   ['30', '05', '32'],
    'TLTC':  ['6f', 'c4', '3a'],
    'DASH':  ['4c', '10'],
    'TDASH': ['8c', '13'],
    'DOGE': ['1e', '16'],
    'TDOGE': ['71', 'c4']
}


def dec_to_dec128(value):
    if isinstance(value, Decimal):
        return Decimal128(value)
    return value


def dec128_to_dec(value):
    if isinstance(value, Decimal128):
        return value.to_decimal()
    return value


def obj_dec128_to_dec(obj: dict) -> dict:
    return {k: dec128_to_dec(v) for k, v in obj.items()}


def obj_dec_to_dec128(obj: dict) -> dict:
    return {k: dec_to_dec128(v) for k, v in obj.items()}


def obj_list_dec128_to_dec(obj_list: List[dict]) -> List[dict]:
    return list(map(obj_dec128_to_dec, obj_list))


def requests_retry_session(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504), session=None):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def make_flask_response(response):
    headers = {'content-type': 'application/json'}
    if isinstance(response, requests.Response):
        return response.content, response.status_code, headers
    if isinstance(response, dict):
        return json.dumps(response), 200, headers
    return response


def is_address_valid(address, currency) -> bool:
    if not address:
        return False

    try:
        if currency in address_prefixes:
            return check_base58_address(address, currency)
    except ValueError:
        pass

    return False


def check_base58_address(address, currency) -> bool:
    return validate_checksum(address) and validate_prefix(address, currency)


def validate_checksum(address) -> bool:
    coinbytes = base58_decode(address, 25)
    return coinbytes[-4:] == sha256(sha256(coinbytes[:-4]).digest()).digest()[:4]


def validate_prefix(address, currency) -> bool:
    prefix = base58_decode(address, 25).hex()[:2]
    return prefix in address_prefixes[currency]


def base58_decode(bc, length):
    digits58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

    n = 0
    for char in bc:
        n = n * 58 + digits58.index(char)
    return n.to_bytes(length, 'big')


def obj_dropna(obj: dict) -> dict:
    return {k: v for k, v in obj.items() if v is not None}


def sign_message(message, key):
    return hmac.new(
        key=codecs.encode(key),
        msg=codecs.encode(message, 'utf-8'),
        digestmod=hashlib.sha512
    ).hexdigest()


def make_mongo_interval_cond(key, start, end):
    conditions = list()
    if start:
        conditions.append({key: {'$gt': start}})
    if end:
        conditions.append({key: {'$lt': end}})
    return conditions


def parse_currency(currency, optional=False):
    if not currency:
        if optional:
            return currency
        raise NotImplementedError

    return currency


def make_response(result=None):
    return dict(
        success=True,
        message='',
        result=result
    )


def mongo_auto_reconnect(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        latest_exception = None
        for attempt in range(3):
            try:
                return f(*args, **kwargs)
            except AutoReconnect as e:
                latest_exception = e
                wait_t = 0.5 * pow(2, attempt)
                logging.warning("mongo_auto_reconnect: waiting %.1f seconds.", wait_t)
                time.sleep(wait_t)
        raise latest_exception
    return wrapper
