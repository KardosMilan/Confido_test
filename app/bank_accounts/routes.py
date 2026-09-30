from flask import Blueprint, render_template, redirect, url_for, request, flash
from pydantic import ValidationError
from app.extensions import db
from app.identifiers import BankAccountIdentifiers, first_error
from app.models import BankAccount, Bank, Currency, ManagedTrusts, AccountType, BankAccountPending, ACCOUNT_FIELDS, copy_fields
from flask_login import login_required, current_user
from datetime import datetime, date

ALLOWED_ROLES = ['Admin', 'Approver']

bank_accounts_bp = Blueprint('bank_accounts', __name__)


def parse_date(value):
    return datetime.strptime(value, '%Y-%m-%d').date() if value else None


def status_for(end_date):
    return 'Active' if end_date is None or end_date >= date.today() else 'Inactive'


def validate_identifiers(form):
    try:
        return BankAccountIdentifiers(
            account_number_iban=form.get('account_number_iban'),
            account_number_pfj=form.get('account_number_pfj'),
        ), None
    except ValidationError as exc:
        return None, first_error(exc)


def fill_account(target, form, identifiers):
    end_date = parse_date(form.get('end_date'))
    target.bank_account_name = form.get('bank_account_name')
    target.account_number_iban = identifiers.account_number_iban
    target.account_number_pfj = identifiers.account_number_pfj
    target.type = form.get('type')
    target.bank_id = form.get('bank_id', type=int)
    target.trust_id = form.get('trust_id', type=int)
    target.currency_id = form.get('currency', type=int)
    target.contract_date = parse_date(form.get('contract_date')) or target.contract_date
    target.end_date = end_date
    target.status = status_for(end_date)
    target.state = "Pending"
    target.inspector_1 = current_user.id
    target.approval_time = datetime.utcnow()


def draft_from_form(form):
    return BankAccountPending(
        bank_account_name=form.get('bank_account_name'),
        account_number_iban=form.get('account_number_iban'),
        account_number_pfj=form.get('account_number_pfj'),
        type=form.get('type'),
        bank_id=form.get('bank_id', type=int),
        trust_id=form.get('trust_id', type=int),
        currency_id=form.get('currency', type=int),
        contract_date=form.get('contract_date'),
        end_date=form.get('end_date'),
    )


def render_account_form(account, title, cancel_url, active_page):
    return render_template(
        'account_form.html',
        account=account,
        title=title,
        cancel_url=cancel_url,
        banks=Bank.query.all(),
        currencies=Currency.query.all(),
        trusts=ManagedTrusts.query.all(),
        account_types=[t.value for t in AccountType],
        active_page=active_page
    )


@bank_accounts_bp.route('/bank-accounts')
@login_required
def bank_accounts():
    accounts = BankAccount.query.all()
    return render_template('bank_accounts.html', accounts=accounts, active_page='bank_accounts')

@bank_accounts_bp.route('/bank-accounts/new', methods=['GET', 'POST'])
@login_required
def new_bank_account():
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('bank_accounts.bank_accounts'))

    title = 'New Bank Account'
    cancel_url = url_for('bank_accounts.bank_accounts')

    if request.method == 'POST':
        identifiers, error = validate_identifiers(request.form)
        if error:
            flash(error, 'danger')
            return render_account_form(draft_from_form(request.form), title, cancel_url, 'new_account')

        new_account = BankAccountPending()
        fill_account(new_account, request.form, identifiers)
        db.session.add(new_account)
        db.session.commit()
        flash('Bank account saved and sent for approval.', 'success')
        return redirect(url_for('bank_accounts.bank_accounts'))

    return render_account_form(None, title, cancel_url, 'new_account')

@bank_accounts_bp.route('/bank-accounts/<int:account_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_bank_account(account_id):
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('bank_accounts.bank_accounts'))

    account = BankAccount.query.get_or_404(account_id)
    change = account.pending_changes[0] if account.pending_changes else None
    title = 'Edit Bank Account'
    cancel_url = url_for('bank_accounts.bank_accounts')

    if request.method == 'POST':
        identifiers, error = validate_identifiers(request.form)
        if error:
            flash(error, 'danger')
            return render_account_form(draft_from_form(request.form), title, cancel_url, 'bank_accounts')

        if change is None:
            change = BankAccountPending(original=account)
            copy_fields(account, change, ACCOUNT_FIELDS)
            db.session.add(change)

        fill_account(change, request.form, identifiers)
        account.state = "Pending"

        db.session.commit()
        flash('Changes saved and sent for approval.', 'success')
        return redirect(url_for('bank_accounts.bank_accounts'))

    return render_account_form(change or account, title, cancel_url, 'bank_accounts')

@bank_accounts_bp.route('/bank-accounts/<int:account_id>/delete', methods=['POST'])
@login_required
def delete_bank_account(account_id):
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('bank_accounts.bank_accounts'))

    account = BankAccount.query.get_or_404(account_id)
    if account.balances or account.pending_balances:
        flash('This account has recorded balances and can not be deleted!', 'danger')
        return redirect(url_for('bank_accounts.bank_accounts'))

    db.session.delete(account)
    db.session.commit()
    return redirect(url_for('bank_accounts.bank_accounts'))

@bank_accounts_bp.route('/bank-accounts-pending/<int:account_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_bank_account_pending(account_id):
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('approvals.approvals', tab='accounts'))

    account = BankAccountPending.query.get_or_404(account_id)
    title = 'Edit Pending Bank Account'
    cancel_url = url_for('approvals.approve_account', account_id=account_id)

    if request.method == 'POST':
        identifiers, error = validate_identifiers(request.form)
        if error:
            flash(error, 'danger')
            return render_account_form(draft_from_form(request.form), title, cancel_url, 'approvals')

        fill_account(account, request.form, identifiers)
        db.session.commit()
        return redirect(url_for('approvals.approvals', tab='accounts'))

    return render_account_form(account, title, cancel_url, 'approvals')

@bank_accounts_bp.route('/bank-accounts-pending/<int:account_id>/delete', methods=['POST'])
@login_required
def delete_account_pending(account_id):
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('bank_accounts.bank_accounts'))

    account = BankAccountPending.query.get_or_404(account_id)
    if account.original:
        account.original.state = "Approved"
    db.session.delete(account)
    db.session.commit()
    return redirect(url_for('approvals.approvals', tab='accounts'))
