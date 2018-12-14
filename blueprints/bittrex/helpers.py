import logging
from pprint import pformat
from flask import jsonify, current_app, request
from functools import wraps

from core.bittrex.types import BittrexApiError

logger = logging.getLogger('testex')


def bittrex_api_method(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            current_app.executor.process()
            current_app.bittrex_stub.switch_user(
                url=request.url,
                nonce=request.args.get('nonce'),
                api_key=request.args.get('apikey'),
                api_sign=request.headers.get('apisign')
            )
            response = f(*args, **kwargs)
            current_app.executor.process()
        except BittrexApiError as e:
            response = e.get_response()
            logger.error('{}: {}\n{}'.format(
                request.path, e.message,
                pformat(request.args if request.method == 'GET' else request.form.to_dict(), compact=True)
            ))
        return jsonify(response)
    return decorated_function
