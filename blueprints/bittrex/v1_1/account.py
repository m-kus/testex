from flask import Blueprint, current_app, request

from blueprints.bittrex.helpers import bittrex_api_method

blueprint = Blueprint('bittrex_account_v1.1', __name__, url_prefix='/bittrex.com/api/v1.1/account')


@blueprint.route('/getbalances')
@bittrex_api_method
def getbalances():
    return current_app.bittrex_stub.get_balances()


@blueprint.route('/getbalance')
@bittrex_api_method
def getbalance():
    return current_app.bittrex_stub.get_balance(
        currency=request.args.get('currency')
    )


@blueprint.route('/getdepositaddress')
@bittrex_api_method
def getdepositaddress():
    return current_app.bittrex_stub.get_deposit_address(
        currency=request.args.get('currency')
    )


@blueprint.route('/withdraw')
@bittrex_api_method
def withdraw():
    return current_app.bittrex_stub.withdraw(
        currency=request.args.get('currency'),
        quantity=request.args.get('quantity'),
        address=request.args.get('address'),
        payment_id=request.args.get('paymentid')
    )


@blueprint.route('/getorder')
@bittrex_api_method
def getorder():
    return current_app.bittrex_stub.get_order(
        uuid=request.args.get('uuid')
    )


@blueprint.route('/getorderhistory')
@bittrex_api_method
def getorderhistory():
    return current_app.bittrex_stub.get_order_history(
        market=request.args.get('market')
    )


@blueprint.route('/getwithdrawalhistory')
@bittrex_api_method
def getwithdrawalhistory():
    return current_app.bittrex_stub.get_withdrawal_history(
        currency=request.args.get('currency')
    )


@blueprint.route('/getdeposithistory')
@bittrex_api_method
def getdeposithistory():
    return current_app.bittrex_stub.get_deposit_history(
        currency=request.args.get('currency')
    )
