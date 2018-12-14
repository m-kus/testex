import requests
from pprint import pformat
from decimal import Decimal
from datetime import datetime

from examples.helpers import PoloniexApi

BASE_URL = 'http://127.0.0.1:8008/'
POLONIEX_API_KEY = 'poloniex_api_key'
CURRENCY = 'BTC'
MIN_AMOUNT = Decimal('100.5')
ADDRESS = '1Nh7uHdvY6fNwtQtM1G5EZAFPLC33B59rB'


def make_deposit(api_key, currency, amount: Decimal):
    data = dict(
        api_key=api_key,
        currency=currency,
        amount=amount
    )
    print('Deposit {}'.format(pformat(data, compact=True)))
    requests.post('http://127.0.0.1:8008/deposit', data=data)


def get_poloniex_balances(trading_api: PoloniexApi):
    result = trading_api.returnBalances()
    print('Poloniex {}'.format(pformat({
        currency: balance
        for currency, balance in result.items()
        if balance > 0
    })))
    return result


def poloniex_toggle_balance():
    poloniex_trading = PoloniexApi(
        base_url='{}poloniex.com/tradingApi'.format(BASE_URL),
        api_key=POLONIEX_API_KEY,
        api_secret=POLONIEX_API_KEY
    )

    balance = get_poloniex_balances(poloniex_trading).get(CURRENCY, Decimal())
    if balance < MIN_AMOUNT:
        make_deposit(
            api_key=POLONIEX_API_KEY,
            currency=CURRENCY,
            amount=MIN_AMOUNT - balance
        )
    else:
        poloniex_trading.withdraw(
            currency=CURRENCY,
            amount=balance,
            address=ADDRESS
        )

    get_poloniex_balances(poloniex_trading)

    transactions = poloniex_trading.returnDepositsWithdrawals(
        start=0,
        end=int(datetime.utcnow().timestamp())
    )
    print('Transactions {}'.format(pformat(transactions, compact=True)))


if __name__ == '__main__':
    poloniex_toggle_balance()
