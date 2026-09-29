from flask import Blueprint, render_template, redirect, url_for, request
from app.extensions import db
from app.models import BankAccount, Bank, Currency, ManagedTrusts, AccountType
from flask_login import login_required

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
        new_account = BankAccount(
            bank_account_name=request.form.get('bank_account_name'),
            account_number_iban=request.form.get('account_number_iban'),
            account_number_pfj=request.form.get('account_number_pfj'),
            type=request.form.get('type'),
            bank_id=request.form.get('bank_id', type=int),
            trust_id=request.form.get('trust_id', type=int),
            currency=request.form.get('currency', type=int),
            status=request.form.get('status', 'Active'),
            active=(request.form.get('status') == 'Active')
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
    account = BankAccount.query.get_or_404(account_id)

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