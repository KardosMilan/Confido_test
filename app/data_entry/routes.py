import calendar
import re
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.formatting import format_amount
from app.models import BankAccount, BankAccountBalance, BankAccountPendingBalance, ManagedTrusts, RiportDate

ALLOWED_ROLES = ['Admin', 'Approver']
HISTORY_MONTHS = 24
BALANCE_STATUSES = ('Missing', 'Pending Approval', 'Approved')

data_entry_bp = Blueprint('data_entry', __name__)


def month_end(day):
    return day.replace(day=calendar.monthrange(day.year, day.month)[1])


def previous_month_end(day):
    return day.replace(day=1) - timedelta(days=1)


def report_date_options():
    latest = previous_month_end(date.today())
    earliest = latest
    for _ in range(HISTORY_MONTHS - 1):
        earliest = previous_month_end(earliest)

    first_contract_date = db.session.query(db.func.min(BankAccount.contract_date)).scalar()
    if first_contract_date:
        earliest = min(earliest, month_end(first_contract_date))

    options = []
    current = latest
    while current >= earliest:
        options.append(current)
        current = previous_month_end(current)
    return options


def parse_date(value):
    try:
        return datetime.strptime(value or '', '%Y-%m-%d').date()
    except ValueError:
        return None


def is_active_on(account, report_date):
    started = account.contract_date is None or account.contract_date <= report_date
    not_ended = account.end_date is None or account.end_date >= report_date
    return started and not_ended


def active_accounts(report_date, trust_id=None):
    query = BankAccount.query
    if trust_id:
        query = query.filter(BankAccount.trust_id == trust_id)
    accounts = query.order_by(BankAccount.bank_account_name).all()
    return [account for account in accounts if is_active_on(account, report_date)]


def currency_decimals(account):
    return account.currency.decimals if account.currency else 2


def quantum(decimals):
    return Decimal(1).scaleb(-decimals)


def parse_amount(value):
    cleaned = re.sub(r'\s', '', value or '').replace(',', '.')
    try:
        amount = Decimal(cleaned)
    except InvalidOperation:
        return None
    return amount if amount.is_finite() else None


def get_or_create_report_date(report_date):
    riport_date = RiportDate.query.filter_by(honap_utolso_napja=report_date).first()
    if riport_date is None:
        riport_date = RiportDate(ev=report_date.year, honap=report_date.month, honap_utolso_napja=report_date)
        db.session.add(riport_date)
        db.session.flush()
    return riport_date


@data_entry_bp.route('/data-entry')
@login_required
def index():
    return redirect(url_for('data_entry.bank_balances'))

@data_entry_bp.route('/data-entry/other')
@login_required
def other_data():
    return render_template('data_entry_other.html', data_entry_tab='other', active_page='data_entry')

@data_entry_bp.route('/data-entry/bank-balances')
@login_required
def bank_balances():
    options = report_date_options()
    report_date = parse_date(request.args.get('report_date'))
    if report_date not in options:
        report_date = options[0]
    trust_id = request.args.get('trust_id', type=int)

    approved = {}
    pending = {}
    riport_date = RiportDate.query.filter_by(honap_utolso_napja=report_date).first()
    if riport_date:
        approved = {b.account_id: b for b in BankAccountBalance.query.filter_by(riport_id=riport_date.riport_id)}
        pending = {b.account_id: b for b in BankAccountPendingBalance.query.filter_by(riport_id=riport_date.riport_id)}

    rows = []
    for account in active_accounts(report_date, trust_id):
        decimals = currency_decimals(account)
        approved_balance = approved.get(account.account_id)
        pending_balance = pending.get(account.account_id)

        if pending_balance:
            status = 'Pending Approval'
        elif approved_balance:
            status = 'Approved'
        else:
            status = 'Missing'

        current = pending_balance or approved_balance
        rows.append({
            'account': account,
            'status': status,
            'decimals': decimals,
            'saved_value': format_amount(current.balance, decimals) if current else '',
        })

    summary = {status: sum(1 for row in rows if row['status'] == status) for status in BALANCE_STATUSES}

    return render_template(
        'bank_balances.html',
        rows=rows,
        summary=summary,
        report_date=report_date,
        report_date_options=options,
        trusts=ManagedTrusts.query.order_by(ManagedTrusts.trust_name).all(),
        trust_id=trust_id,
        can_edit=current_user.role in ALLOWED_ROLES,
        data_entry_tab='bank_balances',
        active_page='data_entry'
    )

@data_entry_bp.route('/data-entry/bank-balances', methods=['POST'])
@login_required
def save_bank_balance():
    trust_id = request.form.get('trust_id', type=int)
    report_date = parse_date(request.form.get('report_date'))
    account_id = request.form.get('account_id', type=int)
    back_url = url_for(
        'data_entry.bank_balances',
        report_date=report_date.isoformat() if report_date else None,
        trust_id=trust_id,
        _anchor=f'account-{account_id}'
    )

    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(back_url)

    if report_date not in report_date_options():
        flash('Please select a valid report date!', 'danger')
        return redirect(back_url)

    account = BankAccount.query.get_or_404(account_id)
    if not is_active_on(account, report_date):
        flash(f'{account.bank_account_name} is not active on {report_date.isoformat()}!', 'danger')
        return redirect(back_url)

    decimals = currency_decimals(account)
    balance = parse_amount(request.form.get('balance'))
    if balance is None:
        flash('Balance must be a number!', 'danger')
        return redirect(back_url)
    if balance < 0:
        flash('Balance can not be negative!', 'danger')
        return redirect(back_url)
    if balance != balance.quantize(quantum(decimals)):
        currency_code = account.currency.code if account.currency else 'This currency'
        flash(f'{currency_code} balances can have at most {decimals} decimal places!', 'danger')
        return redirect(back_url)

    riport_date = get_or_create_report_date(report_date)
    pending = db.session.get(BankAccountPendingBalance, (account.account_id, riport_date.riport_id))
    if pending is None:
        pending = BankAccountPendingBalance(account_id=account.account_id, riport_id=riport_date.riport_id)
        db.session.add(pending)

    pending.balance = balance.quantize(quantum(decimals))
    pending.state = "Pending"
    pending.inspector_1 = current_user.id
    pending.approval_time = datetime.utcnow()

    approved = db.session.get(BankAccountBalance, (account.account_id, riport_date.riport_id))
    if approved:
        approved.state = "Pending"

    db.session.commit()
    return redirect(back_url)

@data_entry_bp.route('/data-entry/bank-balances-pending/<int:account_id>/<int:riport_id>/delete', methods=['POST'])
@login_required
def delete_bank_balance_pending(account_id, riport_id):
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('approvals.approvals', tab='balances'))

    pending = BankAccountPendingBalance.query.get_or_404((account_id, riport_id))
    approved = db.session.get(BankAccountBalance, (account_id, riport_id))
    if approved:
        approved.state = "Approved"
    db.session.delete(pending)
    db.session.commit()
    return redirect(url_for('approvals.approvals', tab='balances'))
