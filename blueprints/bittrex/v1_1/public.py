from flask import Blueprint, current_app, request

from core.helpers import make_flask_response

blueprint = Blueprint('bittrex_public_v1.1', __name__, url_prefix='/bittrex.com/api/v1.1/public')


@blueprint.route('/getmarkets', methods=['GET'])
def getmarkets():
    return make_flask_response(current_app.bittrex_stub.get_markets())


@blueprint.route('/getcurrencies', methods=['GET'])
def getcurrencies():
    return make_flask_response(current_app.bittrex_stub.get_currencies())


@blueprint.route('/getticker', methods=['GET'])
def getticker():
    return make_flask_response(current_app.bittrex_stub.get_ticker(
        market=request.args.get('market')
    ))


@blueprint.route('/getmarketsummaries', methods=['GET'])
def getmarketsummaries():
    return make_flask_response(current_app.bittrex_stub.get_market_summaries())


@blueprint.route('/getorderbook', methods=['GET'])
def getorderbook():
    return make_flask_response(current_app.bittrex_stub.get_order_book(
        market=request.args.get('market'),
        _type=request.args.get('type')
    ))


@blueprint.route('/getmarketsummary', methods=['GET'])
def getmarketsummary():
    return make_flask_response(current_app.bittrex_stub.get_market_summary(
        market=request.args.get('market')
    ))


@blueprint.route('/getmarkethistory', methods=['GET'])
def getmarkethistory():
    return make_flask_response(current_app.bittrex_stub.get_market_history(
        market=request.args.get('market')
    ))
