from flask_wtf import FlaskForm
from decimal import Decimal
from wtforms import StringField, SubmitField, DecimalField
from wtforms.validators import DataRequired


class DepositForm(FlaskForm):
    api_key = StringField('API Key', validators=[DataRequired()], default='qwerty')
    amount = DecimalField('Amount', validators=[DataRequired()], default=Decimal('1'))
    currency = StringField('Currency', validators=[DataRequired()], default='BTC')
    submit = SubmitField('Deposit')
