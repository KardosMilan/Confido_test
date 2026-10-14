import calendar
import re
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.formatting import format_amount
from app.models import Bank, BankAccount, BankAccountBalance, BankAccountPendingBalance, ManagedTrusts, RiportDate

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


def filtered_accounts(trust_id=None, bank_id=None):
    query = BankAccount.query
    if trust_id:
        query = query.filter(BankAccount.trust_id == trust_id)
    if bank_id:
        query = query.filter(BankAccount.bank_id == bank_id)
    return query.order_by(BankAccount.bank_account_name).all()


def active_accounts(report_date, trust_id=None, bank_id=None):
    return [account for account in filtered_accounts(trust_id, bank_id) if is_active_on(account, report_date)]


def row_anchor(account_id, report_date, view_all):
    return f'account-{account_id}-{report_date.isoformat()}' if view_all else f'account-{account_id}'


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
    selected = request.args.get('report_date', 'all')
    report_date = parse_date(selected)
    view_all = report_date not in options
    report_dates = options if view_all else [report_date]
    trust_id = request.args.get('trust_id', type=int)
    bank_id = request.args.get('bank_id', type=int)

    riport_dates = {
        riport.riport_id: riport.honap_utolso_napja
        for riport in RiportDate.query.filter(RiportDate.honap_utolso_napja.in_(report_dates)).all()
    }
    approved = {
        (balance.account_id, riport_dates[balance.riport_id]): balance
        for balance in BankAccountBalance.query.filter(BankAccountBalance.riport_id.in_(riport_dates)).all()
    }
    pending = {
        (balance.account_id, riport_dates[balance.riport_id]): balance
        for balance in BankAccountPendingBalance.query.filter(BankAccountPendingBalance.riport_id.in_(riport_dates)).all()
    }

    accounts = filtered_accounts(trust_id, bank_id)
    rows = []
    for day in report_dates:
        for account in accounts:
            if not is_active_on(account, day):
                continue
            decimals = currency_decimals(account)
            approved_balance = approved.get((account.account_id, day))
            pending_balance = pending.get((account.account_id, day))

            if pending_balance:
                status = 'Pending Approval'
            elif approved_balance:
                status = 'Approved'
            else:
                status = 'Missing'

            current = pending_balance or approved_balance
            rows.append({
                'account': account,
                'report_date': day,
                'anchor': row_anchor(account.account_id, day, view_all),
                'status': status,
                'decimals': decimals,
                'saved_value': format_amount(current.balance, decimals) if current else '',
            })

    summary = {status: sum(1 for row in rows if row['status'] == status) for status in BALANCE_STATUSES}
    banks = (
        Bank.query
        .join(BankAccount, BankAccount.bank_id == Bank.bank_id)
        .distinct()
        .order_by(Bank.bank_name)
        .all()
    )

    return render_template(
        'bank_balances.html',
        rows=rows,
        summary=summary,
        view_all=view_all,
        report_date=None if view_all else report_date,
        report_date_options=options,
        trusts=ManagedTrusts.query.order_by(ManagedTrusts.trust_name).all(),
        trust_id=trust_id,
        banks=banks,
        bank_id=bank_id,
        can_edit=current_user.role in ALLOWED_ROLES,
        data_entry_tab='bank_balances',
        active_page='data_entry'
    )

@data_entry_bp.route('/data-entry/bank-balances', methods=['POST'])
@login_required
def save_bank_balance():
    trust_id = request.form.get('trust_id', type=int)
    bank_id = request.form.get('bank_id', type=int)
    report_date = parse_date(request.form.get('report_date'))
    account_id = request.form.get('account_id', type=int)
    view_all = request.form.get('view_date') == 'all'
    back_url = url_for(
        'data_entry.bank_balances',
        report_date='all' if view_all else (report_date.isoformat() if report_date else None),
        trust_id=trust_id,
        bank_id=bank_id,
        _anchor=row_anchor(account_id, report_date, view_all) if report_date else None
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
