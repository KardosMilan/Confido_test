from flask import Blueprint, render_template, redirect, url_for, request, flash
from app.extensions import db
from app.models import BankAccount, Bank, Currency, ManagedTrusts, AccountType, BankAccountPending
from flask_login import login_required, current_user
from datetime import datetime, date

ALLOWED_ROLES = ['Admin', 'Approver']

bank_accounts_bp = Blueprint('bank_accounts', __name__)

@bank_accounts_bp.route('/bank-accounts')
@login_required
def bank_accounts():
    accounts = BankAccount.query.all()
    return render_template('bank_accounts.html', accounts=accounts, active_page='bank_accounts')

@bank_accounts_bp.route('/bank-accounts/new', methods=['GET', 'POST'])
@login_required
def new_bank_account():
    if request.method == 'POST':
        date_str = request.form.get('contract_date')
        account_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
                
        end_date_str = request.form.get('end_date')
                
        status = 'Inactive'
                
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
        if end_date == None:
            status = 'Active'
        elif (end_date >= date.today()):
            status = 'Active'

        new_account = BankAccountPending(
            bank_account_name=request.form.get('bank_account_name'),
            account_number_iban=request.form.get('account_number_iban'),
            account_number_pfj=request.form.get('account_number_pfj'),
            type=request.form.get('type'),
            bank_id=request.form.get('bank_id', type=int),
            trust_id=request.form.get('trust_id', type=int),
            currency_id=request.form.get('currency', type=int),
            contract_date=account_date,
            end_date=end_date,
            status=request.form.get('status', 'Active'),
            state="Pending",
            inspector_1=current_user.id
        )
        db.session.add(new_account)
        db.session.commit()
        return redirect(url_for('bank_accounts.bank_accounts'))

    banks = Bank.query.all()
    currencies = Currency.query.all()
    trusts = ManagedTrusts.query.all()
    account_types = [t.value for t in AccountType]
    
    return render_template(
        'account_form.html', 
        account=None, 
        banks=banks, 
        currencies=currencies, 
        trusts=trusts, 
        account_types=account_types,
        active_page='new_account'
    )

@bank_accounts_bp.route('/bank-accounts/<int:account_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_bank_account(account_id):
    account = BankAccountPending.query.get_or_404(account_id)

    if request.method == 'POST':
        account.bank_account_name = request.form.get('bank_account_name')
        account.account_number_iban = request.form.get('account_number_iban')
        account.account_number_pfj = request.form.get('account_number_pfj')
        account.type = request.form.get('type')
        account.bank_id = request.form.get('bank_id', type=int)
        account.trust_id = request.form.get('trust_id', type=int)
        account.currency = request.form.get('currency', type=int)
        account.status = request.form.get('status')
        account.active = (request.form.get('status') == 'Active')
        
        db.session.commit()
        return redirect(url_for('bank_accounts.bank_accounts'))

    banks = Bank.query.all()
    currencies = Currency.query.all()
    trusts = ManagedTrusts.query.all()
    account_types = [t.value for t in AccountType]

    return render_template(
        'account_form.html', 
        account=account, 
        banks=banks, 
        currencies=currencies, 
        trusts=trusts, 
        account_types=account_types,
        active_page='bank_accounts'
    )

@bank_accounts_bp.route('/bank-accounts/<int:account_id>/delete', methods=['POST'])
@login_required
def delete_bank_account(account_id):
    account = BankAccount.query.get_or_404(account_id)
    db.session.delete(account)
    db.session.commit()
    return redirect(url_for('bank_accounts.bank_accounts'))

@bank_accounts_bp.route('/bank-accounts-pending/<int:account_id>/delete', methods=['POST'])
@login_required
def delete_account_pending(account_id):
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('bank_accounts.bank_accounts'))
    
    account = BankAccountPending.query.get_or_404(account_id)
    db.session.delete(account)
    db.session.commit()
    return redirect(url_for('approvals'))