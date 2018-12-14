import logging
from flask import Flask, redirect, url_for
from flask_pymongo import PyMongo
from werkzeug.utils import find_modules
from importlib import import_module

from core.bittrex.stub import BittrexApiStub
from core.poloniex.stub import PoloniexApiStub
from core.executor import SimpleExecutor


def create_app(config='dev', *args, **kwargs):
    app = Flask(import_name=__name__, *args, **kwargs)
    app.config.from_pyfile('config/{}.py'.format(config))

    app.logger.propagate = True
    app.logger.setLevel(logging.DEBUG)

    app.mongo = PyMongo(app=app)

    app.executor = SimpleExecutor(db=app.mongo.db)
    app.poloniex_stub = PoloniexApiStub(executor=app.executor)
    app.bittrex_stub = BittrexApiStub(executor=app.executor)

    for module_name in find_modules('blueprints', recursive=True):
        module = import_module(module_name)
        if hasattr(module, 'blueprint'):
            app.register_blueprint(getattr(module, 'blueprint'))

    @app.errorhandler(404)
    def redirect_to_docs(_e):
        return redirect(url_for('pages.documentation')), 404

    return app


if __name__ == '__main__':
    application = create_app()
    application.run(debug=True)
