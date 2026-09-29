from flask import Blueprint, render_template, redirect, url_for, request, flash
from app.extensions import db
from app.models import BankAccountPending, ManagedTrustsPending, BankAccount, ManagedTrusts, Currency
from flask_login import login_required, current_user

ALLOWED_ROLES = ['Admin', 'Approver']

approvals_bp = Blueprint('approvals', __name__)

@approvals_bp.route('/approvals')
@login_required
def approvals():
    pending_accounts = BankAccountPending.query.all()
    pending_trusts = ManagedTrustsPending.query.all()
    return render_template('approvals.html', accounts=pending_accounts, trusts=pending_trusts, active_page='approvals')

@approvals_bp.route('/approvals/account/<int:account_id>/approve', methods=['POST'])
@login_required
def approve_account(account_id):
    pending = BankAccountPending.query.get_or_404(account_id)

    if current_user.role not in ALLOWED_ROLES:
            flash('No permission granted!', 'danger')
            return redirect(url_for('approvals.approvals'))
    
    approved_account = BankAccount(
        trust_id=pending.trust_id,
        bank_id=pending.bank_id,
        type=pending.type,
        account_number_iban=pending.account_number_iban,
        account_number_pfj=pending.account_number_pfj,
        bank_account_name=pending.bank_account_name,
        active=True,
        status='Active',
        inspector_1=pending.inspector_1,
        inspector_2=pending.inspector_2
    )
    
    db.session.add(approved_account)
    db.session.delete(pending)
    db.session.commit()
    
    return redirect(url_for('approvals.approvals'))

@approvals_bp.route('/approvals/trust/<int:trust_id>/approve', methods=['GET', 'POST'])
@login_required
def approve_trust(trust_id):
    pending_trust = ManagedTrustsPending.query.get_or_404(trust_id)

    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('approvals.approvals'))

    if (current_user.id == pending_trust.inspector_1) or (current_user.role!="Admin"):
            flash('You can not approve your own trust!', 'danger')
            return redirect(url_for('approvals.approvals'))

    if request.method == 'POST':
        approved_trust = ManagedTrusts(
            trust_name=pending_trust.trust_name,
            contract_number=pending_trust.contract_number,
            tax_number=pending_trust.tax_number,
            contract_date=pending_trust.contract_date,
            end_date=pending_trust.end_date,
            riporting_currency=pending_trust.riporting_currency,
            status=pending_trust.status,
            state="Approved",
            inspector_1=pending_trust.inspector_1,
            inspector_2=current_user.id
        )

        db.session.add(approved_trust)
        db.session.delete(pending_trust)
        db.session.commit()

        return redirect(url_for('approvals.approvals'))

    currencies = Currency.query.all()
    return render_template(
        'approve_trust.html', 
        trust=pending_trust, 
        currencies=currencies, 
        active_page='approvals'
    )