from os.path import dirname
from flask_testing import TestCase
from bson import Decimal128
from decimal import Decimal

from app import create_app


def decimal128_add(self, x):
    if isinstance(x, Decimal128):
        value = x.to_decimal()
    else:
        value = Decimal(x)
    return Decimal128(self.to_decimal() + value)


def patch_decimal128():
    if not hasattr(Decimal128, '__add__'):
        Decimal128.__add__ = decimal128_add
    if not hasattr(Decimal128, '__radd__'):
        Decimal128.__radd__ = decimal128_add


class FlaskTestCase(TestCase):

    def create_app(self):
        return create_app('unittest', root_path=dirname(dirname(__file__)))
