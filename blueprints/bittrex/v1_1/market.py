from flask import Blueprint, current_app, request

from blueprints.bittrex.helpers import bittrex_api_method
from core.schema import OrderDirection

blueprint = Blueprint('bittrex_market_v1.1', __name__, url_prefix='/bittrex.com/api/v1.1/market')


@blueprint.route('/buylimit', methods=['GET'])
@bittrex_api_method
def buylimit():
    return current_app.bittrex_stub.send_order(
        direction=OrderDirection.BUY,
        market=request.args.get('market'),
        quantity=request.args.get('quantity'),
        rate=request.args.get('rate')
    )


@blueprint.route('/selllimit')
@bittrex_api_method
def selllimit():
    return current_app.bittrex_stub.send_order(
        direction=OrderDirection.SELL,
        market=request.args.get('market'),
        quantity=request.args.get('quantity'),
        rate=request.args.get('rate')
    )


@blueprint.route('/cancel')
@bittrex_api_method
def cancel():
    return current_app.bittrex_stub.cancel(
        uuid=request.args.get('uuid')
    )


@blueprint.route('/getopenorders')
@bittrex_api_method
def getopenorders():
    return current_app.bittrex_stub.get_open_orders(
        market=request.args.get('market')
    )
