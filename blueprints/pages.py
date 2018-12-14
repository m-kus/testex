import os
import mistune
from flask import Blueprint, current_app, render_template, flash
from blueprints.forms import DepositForm

blueprint = Blueprint('pages', __name__, url_prefix='')


@blueprint.route('/')
def documentation():
    with open(os.path.join(current_app.root_path, 'README.md')) as file:
        readme = mistune.markdown(file.read())

    return render_template('documentation.html', readme=readme)


@blueprint.route('/deposit', methods=['GET', 'POST'])
def deposit():
    form = DepositForm()
    if form.validate_on_submit():
        current_app.executor.deposit(
            api_key=form.api_key.data,
            currency=form.currency.data,
            quantity=form.amount.data
        )
        flash('{} {} deposited on {}'.format(form.amount.data, form.currency.data, form.api_key.data))
    return render_template('deposit.html', form=form)
