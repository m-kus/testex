from flask import Blueprint, request, current_app, jsonify

from core.poloniex.types import PoloniexErrorMessage
from core.helpers import make_flask_response

blueprint = Blueprint('poloniex_public_v1.0', __name__, url_prefix='/poloniex.com')


@blueprint.route('/public', methods=['GET'])
def public():
    command = request.args.get('command')
    if command == 'returnTicker':
        response = current_app.poloniex_stub.return_ticker()
    elif command == 'return24hVolume':
        response = current_app.poloniex_stub.return_24h_volume()
    elif command == 'returnOrderBook':
        response = current_app.poloniex_stub.return_order_book(
            currency_pair=request.args.get('currencyPair'),
            depth=request.args.get('depth')
        )
    elif command == 'returnTradeHistory':
        response = current_app.poloniex_stub.return_trade_history(
            currency_pair=request.args.get('currencyPair'),
            start=request.args.get('start'),
            end=request.args.get('end')
        )
    elif command == 'returnChartData':
        response = current_app.poloniex_stub.return_chart_data(
            currency_pair=request.args.get('currencyPair'),
            start=request.args.get('start'),
            end=request.args.get('end'),
            period=request.args.get('period')
        )
    elif command == 'returnCurrencies':
        response = current_app.poloniex_stub.return_currencies()
    elif command == 'returnLoanOrders':
        response = current_app.poloniex_stub.return_loan_orders(
            currency=request.args.get('currency')
        )
    else:
        return jsonify(dict(error=PoloniexErrorMessage.INVALID_COMMAND))

    return make_flask_response(response)
