from flask import Blueprint, render_template, redirect, url_for, request, flash
from datetime import datetime, date
from app.extensions import db
from app.models import ManagedTrusts, ManagedTrustsPending, Currency
from flask_login import login_required, current_user

ALLOWED_ROLES = ['Admin', 'Approver']

managed_trusts_bp = Blueprint('managed_trusts', __name__)

@managed_trusts_bp.route('/managed-trusts')
@login_required
def managed_trusts():
    trusts = ManagedTrusts.query.all()
    return render_template('managed_trusts.html', trusts=trusts, active_page='managed_trusts')

@managed_trusts_bp.route('/managed-trusts/new', methods=['GET', 'POST'])
@login_required
def new_managed_trust():
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('managed_trusts.managed_trusts'))
    
    if request.method == 'POST':
        date_str = request.form.get('contract_date')
        trust_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None

        end_date_str = request.form.get('end_date')

        # Státusz kiszámítása
        status = 'Inactive'
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            if end_date >= date.today():
                status = 'Active'

        new_trust = ManagedTrustsPending(
            trust_name=request.form.get('trust_name'),
            contract_number=request.form.get('contract_number'),
            tax_number=request.form.get('tax_number'),
            contract_date=trust_date,
            end_date=end_date,
            riporting_currency=request.form.get('riporting_currency'),
            status=status,
            state="Pending",
            inspector_1=current_user.id
        )
        db.session.add(new_trust)
        db.session.commit()
        return redirect(url_for('managed_trusts.managed_trusts'))

    currencies = Currency.query.all()
    statuses = ["Active", "Inactive"]
    return render_template('trusts_form.html', trust=None, currencies=currencies, statuses=statuses, active_page='managed_trusts')

@managed_trusts_bp.route('/managed-trusts/<int:trust_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_managed_trusts(trust_id):
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('managed_trusts.managed_trusts'))
    
    trust = ManagedTrusts.query.get_or_404(trust_id)

    if request.method == 'POST':
        date_str = request.form.get('date')
        trust.trust_name = request.form.get('trust_name')
        trust.contract_number = request.form.get('contract_number')
        trust.tax_number = request.form.get('tax_number')
        trust.contract_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else trust.contract_date
        trust.end_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else trust.end_date
        trust.riporting_currency = request.form.get('riporting_currency', type=int)
        trust.status = request.form.get('status')
        trust.state="Pending"
        trust.inspector_1=current_user.id

        db.session.commit()
        return redirect(url_for('managed_trusts.managed_trusts'))

    currencies = Currency.query.all()
    statuses = ["Active", "Inactive"]
    return render_template('trusts_form.html', trust=trust, currencies=currencies, statuses=statuses, active_page='managed_trusts')

@managed_trusts_bp.route('/managed-trusts/<int:trust_id>/delete', methods=['POST'])
@login_required
def delete_managed_trusts(trust_id):
    trust = ManagedTrusts.query.get_or_404(trust_id)
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('managed_trusts.managed_trusts'))

    db.session.delete(trust)
    db.session.commit()
    return redirect(url_for('managed_trusts.managed_trusts'))

@managed_trusts_bp.route('/managed-trusts-pending/<int:trust_id>/delete', methods=['POST'])
@login_required
def delete_managed_trusts_pending(trust_id):
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('managed_trusts.managed_trusts'))
    
    trust = ManagedTrustsPending.query.get_or_404(trust_id)
    db.session.delete(trust)
    db.session.commit()
    return redirect(url_for('approvals'))