from flask import Blueprint, render_template, redirect, url_for, request, flash
from datetime import datetime, date
from app.extensions import db
from app.models import ManagedTrusts, ManagedTrustsPending, Currency, TRUST_FIELDS, copy_fields
from flask_login import login_required, current_user

ALLOWED_ROLES = ['Admin', 'Approver']

managed_trusts_bp = Blueprint('managed_trusts', __name__)


def parse_date(value):
    return datetime.strptime(value, '%Y-%m-%d').date() if value else None


def status_for(end_date):
    return 'Active' if end_date is None or end_date >= date.today() else 'Inactive'


def fill_trust(target, form):
    end_date = parse_date(form.get('end_date'))
    target.trust_name = form.get('trust_name')
    target.contract_number = form.get('contract_number')
    target.tax_number = form.get('tax_number')
    target.contract_date = parse_date(form.get('contract_date')) or target.contract_date
    target.end_date = end_date
    target.riporting_currency = form.get('riporting_currency', type=int)
    target.status = status_for(end_date)
    target.state = "Pending"
    target.inspector_1 = current_user.id
    target.approval_time = datetime.utcnow()


def render_trust_form(trust, title, form_action, cancel_url, active_page):
    return render_template(
        'trusts_form.html',
        trust=trust,
        title=title,
        form_action=form_action,
        cancel_url=cancel_url,
        currencies=Currency.query.all(),
        active_page=active_page
    )


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
        new_trust = ManagedTrustsPending()
        fill_trust(new_trust, request.form)
        db.session.add(new_trust)
        db.session.commit()
        flash('Trust saved and sent for approval.', 'success')
        return redirect(url_for('managed_trusts.managed_trusts'))

    return render_trust_form(
        None,
        'New Managed Trust',
        url_for('managed_trusts.new_managed_trust'),
        url_for('managed_trusts.managed_trusts'),
        'managed_trusts'
    )

@managed_trusts_bp.route('/managed-trusts/<int:trust_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_managed_trusts(trust_id):
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('managed_trusts.managed_trusts'))

    trust = ManagedTrusts.query.get_or_404(trust_id)
    change = trust.pending_changes[0] if trust.pending_changes else None

    if request.method == 'POST':
        if change is None:
            change = ManagedTrustsPending(original=trust)
            copy_fields(trust, change, TRUST_FIELDS)
            db.session.add(change)

        fill_trust(change, request.form)
        trust.state = "Pending"

        db.session.commit()
        flash('Changes saved and sent for approval.', 'success')
        return redirect(url_for('managed_trusts.managed_trusts'))

    return render_trust_form(
        change or trust,
        'Edit Managed Trust',
        url_for('managed_trusts.edit_managed_trusts', trust_id=trust_id),
        url_for('managed_trusts.managed_trusts'),
        'managed_trusts'
    )

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

@managed_trusts_bp.route('/managed-trusts-pending/<int:trust_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_managed_trusts_pending(trust_id):
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('approvals.approvals'))

    trust = ManagedTrustsPending.query.get_or_404(trust_id)

    if request.method == 'POST':
        fill_trust(trust, request.form)
        db.session.commit()
        return redirect(url_for('approvals.approvals'))

    return render_trust_form(
        trust,
        'Edit Pending Trust',
        url_for('managed_trusts.edit_managed_trusts_pending', trust_id=trust_id),
        url_for('approvals.approve_trust', trust_id=trust_id),
        'approvals'
    )

@managed_trusts_bp.route('/managed-trusts-pending/<int:trust_id>/delete', methods=['POST'])
@login_required
def delete_managed_trusts_pending(trust_id):
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('managed_trusts.managed_trusts'))

    trust = ManagedTrustsPending.query.get_or_404(trust_id)
    if trust.original:
        trust.original.state = "Approved"
    db.session.delete(trust)
    db.session.commit()
    return redirect(url_for('approvals.approvals'))
