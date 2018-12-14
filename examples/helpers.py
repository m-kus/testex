import codecs
import hashlib
import hmac
from datetime import datetime
from pprint import pformat
from urllib.parse import urljoin, urlencode

import requests
import simplejson as json


def obj_dropna(obj: dict) -> dict:
    return {k: v for k, v in obj.items() if v is not None}


def sign_message(message, key):
    return hmac.new(
        key=codecs.encode(key),
        msg=codecs.encode(message, 'utf-8'),
        digestmod=hashlib.sha512
    ).hexdigest()


class BaseApi:

    def __init__(self, base_url, api_key=None, api_secret=None):
        self.base_url = base_url
        self.api_key = api_key
        self.api_secret = api_secret
        self.last_nonce = 0

    def get_nonce(self):
        nonce = int(1000 * datetime.utcnow().timestamp())
        if nonce == self.last_nonce:
            nonce += 1
        self.last_nonce = nonce
        return nonce

    def request(self, method, **kwargs):
        raise NotImplementedError

    def __getattr__(self, method):
        def wrapper(**kwargs):
            return self.request(method, **kwargs)
        return wrapper


class BittrexApi(BaseApi):

    def request(self, method, **kwargs):
        url = urljoin(self.base_url, method)
        headers = {'Content-Type': 'application/json'}
        params = obj_dropna(kwargs)

        if self.api_key:
            print('{} {}'.format(self.__class__.__name__, pformat(dict(method=method, **params))))
            params.update(
                nonce=self.get_nonce(),
                apikey=self.api_key
            )
            headers.update(
                apisign=sign_message('{}?{}'.format(url, urlencode(params)), key=self.api_secret)
            )

        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            raise requests.ConnectionError(response.status_code)

        data = json.loads(response.text, use_decimal=True)
        if not data['success']:
            raise ValueError(data.get('message', data))

        return data['result']


class PoloniexApi(BaseApi):

    def request(self, method, **params):
        params = obj_dropna(params)
        params.update(command=method)

        if self.api_key:
            print('{} {}'.format(self.__class__.__name__, pformat(dict(**params))))
            data = dict(
                nonce=self.get_nonce(),
                **params
            )
            headers = dict(
                Key=self.api_key,
                Sign=sign_message(urlencode(data), key=self.api_secret)
            )
            response = requests.post(self.base_url, data=data, headers=headers)
        else:
            response = requests.get(self.base_url, params=params)

        if response.status_code != 200:
            raise requests.ConnectionError(response.status_code)

        data = json.loads(response.text, use_decimal=True)
        if 'error' in data:
            raise ValueError(data['error'])

        return data
