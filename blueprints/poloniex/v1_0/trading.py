from flask import Blueprint, current_app, request

from blueprints.poloniex.helpers import poloniex_api_method, prevent_form_parse
from core.poloniex.types import PoloniexErrorMessage, PoloniexApiError
from core.schema import OrderDirection

blueprint = Blueprint('poloniex_trading_v1.0', __name__, url_prefix='/poloniex.com')
blueprint.before_request(prevent_form_parse)


@blueprint.route('/tradingApi', methods=['POST'])
@poloniex_api_method
def trading_api():
    command = request.form.get('command')
    if command == 'returnBalances':
        response = current_app.poloniex_stub.return_balances()
    elif command == 'returnCompleteBalances':
        response = current_app.poloniex_stub.return_complete_balances(
            account=request.form.get('account')
        )
    elif command == 'returnDepositAddresses':
        response = current_app.poloniex_stub.return_deposit_addresses()
    elif command == 'generateNewAddress':
        response = current_app.poloniex_stub.generate_new_address(
            currency=request.form.get('currency')
        )
    elif command == 'returnDepositsWithdrawals':
        response = current_app.poloniex_stub.return_deposits_withdrawals(
            start=request.form.get('start'),
            end=request.form.get('end')
        )
    elif command == 'returnOpenOrders':
        response = current_app.poloniex_stub.return_open_orders(
            currency_pair=request.form.get('currencyPair')
        )
    elif command == 'returnTradeHistory':
        response = current_app.poloniex_stub.return_account_trade_history(
            currency_pair=request.form.get('currencyPair'),
            start=request.form.get('start'),
            end=request.form.get('end'),
            limit=request.form.get('limit')
        )
    elif command == 'returnOrderTrades':
        response = current_app.poloniex_stub.return_order_trades(
            order_number=request.form.get('orderNumber')
        )
    elif command == 'returnOrderStatus':
        response = current_app.poloniex_stub.return_order_status(
            order_number=request.form.get('orderNumber')
        )
    elif command == 'buy':
        response = current_app.poloniex_stub.send_order(
            direction=OrderDirection.BUY,
            currency_pair=request.form.get('currencyPair'),
            rate=request.form.get('rate'),
            amount=request.form.get('amount'),
            fill_or_kill=request.form.get('fillOrKill'),
            immediate_or_cancel=request.form.get('immediateOrCancel'),
            post_only=request.form.get('postOnly')
        )
    elif command == 'sell':
        response = current_app.poloniex_stub.send_order(
            direction=OrderDirection.SELL,
            currency_pair=request.form.get('currencyPair'),
            rate=request.form.get('rate'),
            amount=request.form.get('amount'),
            fill_or_kill=request.form.get('fillOrKill'),
            immediate_or_cancel=request.form.get('immediateOrCancel'),
            post_only=request.form.get('postOnly')
        )
    elif command == 'cancelOrder':
        response = current_app.poloniex_stub.cancel_order(
            order_number=request.form.get('orderNumber')
        )
    elif command == 'moveOrder':
        response = current_app.poloniex_stub.move_order(
            order_number=request.form.get('orderNumber'),
            rate=request.form.get('rate'),
            amount=request.form.get('amount'),
            immediate_or_cancel=request.form.get('immediateOrCancel'),
            post_only=request.form.get('postOnly')
        )
    elif command == 'withdraw':
        response = current_app.poloniex_stub.withdraw(
            currency=request.form.get('currency'),
            amount=request.form.get('amount'),
            address=request.form.get('address'),
            payment_id=request.form.get('paymentId')
        )
    elif command == 'returnFeeInfo':
        response = current_app.poloniex_stub.return_fee_info()
    elif command == 'returnAvailableAccountBalances':
        response = current_app.poloniex_stub.return_available_account_balances(
            account=request.form.get('account')
        )
    else:
        raise PoloniexApiError(PoloniexErrorMessage.INVALID_COMMAND)

    return response
