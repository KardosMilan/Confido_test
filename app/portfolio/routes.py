from datetime import datetime
from decimal import Decimal
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.data_entry.routes import parse_amount
from app.extensions import db
from app.formatting import format_amount
from app.models import (
    AssetType,
    ManagedAssets,
    ManagedTrusts,
    Portfolio,
    PortfolioPending,
    PORTFOLIO_FIELDS,
    TRANSACTION_TYPES,
    copy_fields,
)
from app.validation import parse_form_date

ALLOWED_ROLES = ['Admin', 'Approver']
QUANTITY_DECIMALS = 4
RATE_DECIMALS = 6
FORM_FIELDS = ('trust_id', 'asset_id', 'date', 'transaction', 'asset_number', 'exchange_rate', 'value')

portfolio_bp = Blueprint('portfolio', __name__)


def calculation_mode(asset_type):
    if asset_type == AssetType.BOND.value:
        return 'bond'
    if asset_type == AssetType.EQUITY.value:
        return 'equity'
    return 'value'


def currency_decimals(asset):
    return asset.currency.decimals if asset and asset.currency else 2


def parse_positive(form, field, label, decimals):
    amount = parse_amount(form.get(field))
    if amount is None or amount <= 0:
        return None, f'{label} must be a number greater than zero!'
    if amount != amount.quantize(Decimal(1).scaleb(-decimals)):
        return None, f'{label} can have at most {decimals} decimal places!'
    return amount, None


def validate_portfolio_form(form):
    trust_id = form.get('trust_id', type=int)
    if trust_id is None or db.session.get(ManagedTrusts, trust_id) is None:
        return None, 'Please select a valid trust!'

    asset_id = form.get('asset_id', type=int)
    asset = db.session.get(ManagedAssets, asset_id) if asset_id else None
    if asset is None:
        return None, 'Please select a valid asset!'

    entry_date, error = parse_form_date(form.get('date'), 'Date', required=True)
    if error:
        return None, error

    transaction = form.get('transaction') or 'Buy'
    if transaction not in TRANSACTION_TYPES:
        return None, 'Transaction must be Buy or Sell!'

    asset_number = None
    exchange_rate = None
    if calculation_mode(asset.asset_type) != 'value':
        asset_number, error = parse_positive(form, 'asset_number', 'Asset number', QUANTITY_DECIMALS)
        if error:
            return None, error
        exchange_rate, error = parse_positive(form, 'exchange_rate', 'Exchange rate', RATE_DECIMALS)
        if error:
            return None, error

    value, error = parse_positive(form, 'value', 'Value', currency_decimals(asset))
    if error:
        return None, error

    return {
        'trust_id': trust_id,
        'asset_id': asset_id,
        'date': entry_date,
        'transaction': transaction,
        'asset_number': asset_number,
        'exchange_rate': exchange_rate,
        'value': -value if transaction == 'Sell' else value,
    }, None


def fill_portfolio(target, values):
    for key, value in values.items():
        setattr(target, key, value)
    target.state = "Pending"
    target.inspector_1 = current_user.id
    target.approval_time = datetime.utcnow()


def plain_number(value):
    if value is None:
        return ''
    return format(Decimal(value).normalize(), 'f')


def form_values(item=None, raw=None):
    if raw is not None:
        return {field: raw.get(field, '') for field in FORM_FIELDS}
    if item is None:
        return {field: '' for field in FORM_FIELDS} | {'transaction': 'Buy'}
    return {
        'trust_id': str(item.trust_id),
        'asset_id': str(item.asset_id),
        'date': item.date.isoformat() if item.date else '',
        'transaction': item.transaction or 'Buy',
        'asset_number': plain_number(item.asset_number),
        'exchange_rate': plain_number(item.exchange_rate),
        'value': format_amount(abs(Decimal(item.value)), currency_decimals(item.asset)) if item.value is not None else '',
    }


def render_portfolio_form(values, title, form_action, cancel_url, active_page):
    return render_template(
        'portfolio_form.html',
        values=values,
        title=title,
        form_action=form_action,
        cancel_url=cancel_url,
        trusts=ManagedTrusts.query.order_by(ManagedTrusts.trust_name).all(),
        assets=ManagedAssets.query.order_by(ManagedAssets.asset_name).all(),
        transaction_types=TRANSACTION_TYPES,
        active_page=active_page
    )


@portfolio_bp.route('/portfolio')
@login_required
def portfolio():
    items = Portfolio.query.order_by(Portfolio.date.desc(), Portfolio.portfolio_id.desc()).all()
    return render_template('portfolio.html', items=items, active_page='portfolio')

@portfolio_bp.route('/portfolio/new', methods=['GET', 'POST'])
@login_required
def new_portfolio():
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('portfolio.portfolio'))

    title = 'New Portfolio'
    form_action = url_for('portfolio.new_portfolio')
    cancel_url = url_for('portfolio.portfolio')

    if request.method == 'POST':
        values, error = validate_portfolio_form(request.form)
        if error:
            flash(error, 'danger')
            return render_portfolio_form(form_values(raw=request.form), title, form_action, cancel_url, 'portfolio')

        item = PortfolioPending()
        fill_portfolio(item, values)
        db.session.add(item)
        db.session.commit()
        flash('Portfolio entry saved and sent for approval.', 'success')
        return redirect(url_for('portfolio.portfolio'))

    return render_portfolio_form(form_values(), title, form_action, cancel_url, 'portfolio')

@portfolio_bp.route('/portfolio/<int:portfolio_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_portfolio(portfolio_id):
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('portfolio.portfolio'))

    item = Portfolio.query.get_or_404(portfolio_id)
    change = item.pending_changes[0] if item.pending_changes else None
    title = 'Edit Portfolio'
    form_action = url_for('portfolio.edit_portfolio', portfolio_id=portfolio_id)
    cancel_url = url_for('portfolio.portfolio')

    if request.method == 'POST':
        values, error = validate_portfolio_form(request.form)
        if error:
            flash(error, 'danger')
            return render_portfolio_form(form_values(raw=request.form), title, form_action, cancel_url, 'portfolio')

        if change is None:
            change = PortfolioPending(original=item)
            copy_fields(item, change, PORTFOLIO_FIELDS)
            db.session.add(change)

        fill_portfolio(change, values)
        item.state = "Pending"

        db.session.commit()
        flash('Changes saved and sent for approval.', 'success')
        return redirect(url_for('portfolio.portfolio'))

    return render_portfolio_form(form_values(change or item), title, form_action, cancel_url, 'portfolio')

@portfolio_bp.route('/portfolio/<int:portfolio_id>/delete', methods=['POST'])
@login_required
def delete_portfolio(portfolio_id):
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('portfolio.portfolio'))

    item = Portfolio.query.get_or_404(portfolio_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('portfolio.portfolio'))

@portfolio_bp.route('/portfolio-pending/<int:portfolio_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_portfolio_pending(portfolio_id):
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('approvals.approvals', tab='portfolio'))

    item = PortfolioPending.query.get_or_404(portfolio_id)
    title = 'Edit Pending Portfolio'
    form_action = url_for('portfolio.edit_portfolio_pending', portfolio_id=portfolio_id)
    cancel_url = url_for('approvals.approve_portfolio', portfolio_id=portfolio_id)

    if request.method == 'POST':
        values, error = validate_portfolio_form(request.form)
        if error:
            flash(error, 'danger')
            return render_portfolio_form(form_values(raw=request.form), title, form_action, cancel_url, 'approvals')

        fill_portfolio(item, values)
        db.session.commit()
        return redirect(url_for('approvals.approvals', tab='portfolio'))

    return render_portfolio_form(form_values(item), title, form_action, cancel_url, 'approvals')

@portfolio_bp.route('/portfolio-pending/<int:portfolio_id>/delete', methods=['POST'])
@login_required
def delete_portfolio_pending(portfolio_id):
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('approvals.approvals', tab='portfolio'))

    item = PortfolioPending.query.get_or_404(portfolio_id)
    if item.original:
        item.original.state = "Approved"
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('approvals.approvals', tab='portfolio'))
