from flask import Blueprint, render_template, redirect, url_for, request, flash
from datetime import datetime, date
from app.extensions import db
from app.models import ManagedTrusts, ManagedTrustsPending, Currency, Portfolio, PortfolioPending, TRUST_FIELDS, copy_fields
from app.validation import parse_form_date
from flask_login import login_required, current_user

ALLOWED_ROLES = ['Admin', 'Approver']

managed_trusts_bp = Blueprint('managed_trusts', __name__)


def status_for(end_date):
    return 'Active' if end_date is None or end_date >= date.today() else 'Inactive'


def validate_trust_dates(form):
    contract_date, error = parse_form_date(form.get('contract_date'), 'Contract date')
    if error:
        return None, error
    end_date, error = parse_form_date(form.get('end_date'), 'End of management date')
    if error:
        return None, error
    return (contract_date, end_date), None


def draft_from_form(form):
    return ManagedTrustsPending(
        trust_name=form.get('trust_name'),
        contract_number=form.get('contract_number'),
        tax_number=form.get('tax_number'),
        contract_date=form.get('contract_date'),
        end_date=form.get('end_date'),
        riporting_currency=form.get('riporting_currency', type=int),
    )


def fill_trust(target, form, dates):
    contract_date, end_date = dates
    target.trust_name = form.get('trust_name')
    target.contract_number = form.get('contract_number')
    target.tax_number = form.get('tax_number')
    target.contract_date = contract_date or target.contract_date
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
        dates, error = validate_trust_dates(request.form)
        if error:
            flash(error, 'danger')
            return render_trust_form(
                draft_from_form(request.form),
                'New Managed Trust',
                url_for('managed_trusts.new_managed_trust'),
                url_for('managed_trusts.managed_trusts'),
                'managed_trusts'
            )

        new_trust = ManagedTrustsPending()
        fill_trust(new_trust, request.form, dates)
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
        dates, error = validate_trust_dates(request.form)
        if error:
            flash(error, 'danger')
            return render_trust_form(
                draft_from_form(request.form),
                'Edit Managed Trust',
                url_for('managed_trusts.edit_managed_trusts', trust_id=trust_id),
                url_for('managed_trusts.managed_trusts'),
                'managed_trusts'
            )

        if change is None:
            change = ManagedTrustsPending(original=trust)
            copy_fields(trust, change, TRUST_FIELDS)
            db.session.add(change)

        fill_trust(change, request.form, dates)
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

    if trust.portfolio_items or PortfolioPending.query.filter_by(trust_id=trust_id).first():
        flash('This trust has portfolio entries and can not be deleted!', 'danger')
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
        dates, error = validate_trust_dates(request.form)
        if error:
            flash(error, 'danger')
            return render_trust_form(
                draft_from_form(request.form),
                'Edit Pending Trust',
                url_for('managed_trusts.edit_managed_trusts_pending', trust_id=trust_id),
                url_for('approvals.approve_trust', trust_id=trust_id),
                'approvals'
            )

        fill_trust(trust, request.form, dates)
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
