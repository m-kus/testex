import logging
from pprint import pformat
from flask import jsonify, current_app, request, abort
from functools import wraps

from core.poloniex.types import PoloniexApiError

logger = logging.getLogger('testex')


def prevent_form_parse():
    if request.content_length > 1024 * 1024:
        abort(413)
    request.get_data(parse_form_data=False, cache=True)


def poloniex_api_method(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            current_app.executor.process()
            current_app.poloniex_stub.switch_user(
                data=request.get_data(as_text=True),
                api_key=request.headers.get('Key'),
                api_sign=request.headers.get('Sign'),
                nonce=request.form.get('nonce')
            )
            response = f(*args, **kwargs)
            current_app.executor.process()
        except PoloniexApiError as e:
            response = e.get_response()
            logger.error('{}: {}\n{}'.format(
                request.path, e.message,
                pformat(request.args if request.method == 'GET' else request.form.to_dict(), compact=True)
            ))
        return jsonify(response)
    return decorated_function
