import calendar
from datetime import datetime
from decimal import Decimal
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.data_entry.routes import parse_amount
from app.extensions import db
from app.formatting import format_rate
from app.models import Currency, ExchangeRate, ExchangeRateUpdate
from app.validation import parse_form_date

ALLOWED_ROLES = ['Admin', 'Approver']
RATE_DECIMALS = 6
RECENT_FAILURES = 10

exchange_rates_bp = Blueprint('exchange_rates', __name__)


def update_status():
    last_success = (
        ExchangeRateUpdate.query
        .filter_by(status='Success')
        .order_by(ExchangeRateUpdate.run_at.desc())
        .first()
    )
    failures = ExchangeRateUpdate.query.filter_by(status='Failed')
    if last_success:
        failures = failures.filter(ExchangeRateUpdate.run_at > last_success.run_at)
    return last_success, failures.order_by(ExchangeRateUpdate.run_at.desc()).limit(RECENT_FAILURES).all()


def validate_rate_form(form, rate_id=None):
    values = {
        'currency_id': form.get('currency_id', type=int),
        'rate_date': None,
        'rate': None,
    }

    currency = db.session.get(Currency, values['currency_id']) if values['currency_id'] else None
    if currency is None or currency.code == 'HUF':
        return values, 'Please select a valid foreign currency!'

    values['rate_date'], error = parse_form_date(form.get('rate_date'), 'Report date', required=True)
    if error:
        return values, error
    last_day = calendar.monthrange(values['rate_date'].year, values['rate_date'].month)[1]
    if values['rate_date'].day != last_day:
        return values, 'Exchange rates are stored for month-end report dates!'

    values['rate'] = parse_amount(form.get('rate'))
    if values['rate'] is None or values['rate'] <= 0:
        return values, 'Rate must be a number greater than zero!'
    if values['rate'] != values['rate'].quantize(Decimal(1).scaleb(-RATE_DECIMALS)):
        return values, f'Rate can have at most {RATE_DECIMALS} decimal places!'

    duplicate = ExchangeRate.query.filter_by(currency_id=values['currency_id'], rate_date=values['rate_date']).first()
    if duplicate is not None and duplicate.rate_id != rate_id:
        return values, f'A {currency.code}/HUF rate for {values["rate_date"].isoformat()} already exists!'

    return values, None


def form_values(rate=None, raw=None):
    if raw is not None:
        return {
            'currency_id': raw.get('currency_id', type=int),
            'rate_date': raw.get('rate_date', ''),
            'rate': raw.get('rate', ''),
        }
    if rate is None:
        return {'currency_id': None, 'rate_date': '', 'rate': ''}
    return {
        'currency_id': rate.currency_id,
        'rate_date': rate.rate_date.isoformat(),
        'rate': format_rate(rate.rate),
    }


def render_rate_form(rate, title, form_action, raw=None):
    return render_template(
        'exchange_rate_form.html',
        values=form_values(rate, raw),
        title=title,
        form_action=form_action,
        currencies=Currency.query.filter(Currency.code != 'HUF').order_by(Currency.code).all(),
        data_tab='exchange_rates',
        active_page='data'
    )


@exchange_rates_bp.route('/data/exchange-rates')
@login_required
def exchange_rates():
    rates = (
        ExchangeRate.query
        .join(Currency, ExchangeRate.currency_id == Currency.id)
        .order_by(ExchangeRate.rate_date.desc(), Currency.code)
        .all()
    )
    last_success, failures = update_status()
    return render_template(
        'exchange_rates.html',
        rates=rates,
        last_success=last_success,
        failures=failures,
        data_tab='exchange_rates',
        active_page='data'
    )

@exchange_rates_bp.route('/data/exchange-rates/new', methods=['GET', 'POST'])
@login_required
def new_exchange_rate():
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('exchange_rates.exchange_rates'))

    title = 'New Exchange Rate'
    form_action = url_for('exchange_rates.new_exchange_rate')

    if request.method == 'POST':
        values, error = validate_rate_form(request.form)
        if error:
            flash(error, 'danger')
            return render_rate_form(None, title, form_action, request.form)

        rate = ExchangeRate(**values, source='Manual', updated_at=datetime.utcnow(), updated_by=current_user.id)
        db.session.add(rate)
        db.session.commit()
        flash('Exchange rate saved.', 'success')
        return redirect(url_for('exchange_rates.exchange_rates'))

    return render_rate_form(None, title, form_action)

@exchange_rates_bp.route('/data/exchange-rates/<int:rate_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_exchange_rate(rate_id):
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('exchange_rates.exchange_rates'))

    rate = ExchangeRate.query.get_or_404(rate_id)
    title = 'Edit Exchange Rate'
    form_action = url_for('exchange_rates.edit_exchange_rate', rate_id=rate_id)

    if request.method == 'POST':
        values, error = validate_rate_form(request.form, rate_id=rate_id)
        if error:
            flash(error, 'danger')
            return render_rate_form(rate, title, form_action, request.form)

        for key, value in values.items():
            setattr(rate, key, value)
        rate.source = 'Manual'
        rate.updated_at = datetime.utcnow()
        rate.updated_by = current_user.id

        db.session.commit()
        flash('Exchange rate updated.', 'success')
        return redirect(url_for('exchange_rates.exchange_rates'))

    return render_rate_form(rate, title, form_action)

@exchange_rates_bp.route('/data/exchange-rates/<int:rate_id>/delete', methods=['POST'])
@login_required
def delete_exchange_rate(rate_id):
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('exchange_rates.exchange_rates'))

    rate = ExchangeRate.query.get_or_404(rate_id)
    db.session.delete(rate)
    db.session.commit()
    return redirect(url_for('exchange_rates.exchange_rates'))
