from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash
from app.extensions import db
from app.models import (
    BankAccountPending,
    ManagedTrustsPending,
    BankAccount,
    ManagedTrusts,
    Currency,
    ManagedAssets,
    ManagedAssetsPending,
    ASSET_TYPE_FIELDS,
    BankAccountBalance,
    BankAccountPendingBalance,
    RiportDate,
    TRUST_FIELDS,
    ACCOUNT_FIELDS,
    ASSET_FIELDS,
    copy_fields,
)
from flask_login import login_required, current_user

ALLOWED_ROLES = ['Admin', 'Approver']
APPROVAL_TABS = ('trusts', 'accounts', 'assets', 'balances')

approvals_bp = Blueprint('approvals', __name__)


def apply_pending(pending, model, fields):
    target = pending.original or model()
    copy_fields(pending, target, fields)
    target.state = "Approved"
    target.inspector_1 = pending.inspector_1
    target.inspector_2 = current_user.id
    target.approval_time = datetime.utcnow()

    if pending.original is None:
        db.session.add(target)
    db.session.delete(pending)
    db.session.commit()


@approvals_bp.route('/approvals')
@login_required
def approvals():
    pending_accounts = BankAccountPending.query.all()
    pending_trusts = ManagedTrustsPending.query.all()
    pending_assets = ManagedAssetsPending.query.all()
    pending_balances = (
        BankAccountPendingBalance.query
        .join(RiportDate)
        .order_by(RiportDate.honap_utolso_napja.desc())
        .all()
    )
    riport_ids = {balance.riport_id for balance in pending_balances}
    approved_balances = {
        (balance.account_id, balance.riport_id): balance
        for balance in BankAccountBalance.query.filter(BankAccountBalance.riport_id.in_(riport_ids)).all()
    }
    return render_template(
        'approvals.html',
        accounts=pending_accounts,
        trusts=pending_trusts,
        assets=pending_assets,
        balances=pending_balances,
        approved_balances=approved_balances,
        active_tab=request.args.get('tab') if request.args.get('tab') in APPROVAL_TABS else 'trusts',
        active_page='approvals'
    )

@approvals_bp.route('/approvals/account/<int:account_id>/approve', methods=['GET', 'POST'])
@login_required
def approve_account(account_id):
    pending_account = BankAccountPending.query.get_or_404(account_id)

    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('approvals.approvals', tab='accounts'))

    if (current_user.role != 'Admin') and (current_user.id == pending_account.inspector_1):
        flash('You can not approve your own account!', 'danger')
        return redirect(url_for('approvals.approvals', tab='accounts'))

    if request.method == 'POST':
        apply_pending(pending_account, BankAccount, ACCOUNT_FIELDS)
        return redirect(url_for('approvals.approvals', tab='accounts'))

    return render_template(
        'approve_account.html',
        account=pending_account,
        original=pending_account.original,
        active_page='approvals'
    )

@approvals_bp.route('/approvals/trust/<int:trust_id>/approve', methods=['GET', 'POST'])
@login_required
def approve_trust(trust_id):
    pending_trust = ManagedTrustsPending.query.get_or_404(trust_id)

    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('approvals.approvals'))

    if (current_user.role != 'Admin') and (current_user.id == pending_trust.inspector_1):
        flash('You can not approve your own trust!', 'danger')
        return redirect(url_for('approvals.approvals'))

    if request.method == 'POST':
        apply_pending(pending_trust, ManagedTrusts, TRUST_FIELDS)
        return redirect(url_for('approvals.approvals'))

    return render_template(
        'approve_trust.html',
        trust=pending_trust,
        original=pending_trust.original,
        currencies=Currency.query.all(),
        active_page='approvals'
    )

@approvals_bp.route('/approvals/asset/<int:asset_id>/approve', methods=['GET', 'POST'])
@login_required
def approve_asset(asset_id):
    pending_asset = ManagedAssetsPending.query.get_or_404(asset_id)

    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('approvals.approvals', tab='assets'))

    if (current_user.role != 'Admin') and (current_user.id == pending_asset.inspector_1):
        flash('You can not approve your own asset!', 'danger')
        return redirect(url_for('approvals.approvals', tab='assets'))

    if request.method == 'POST':
        apply_pending(pending_asset, ManagedAssets, ASSET_FIELDS)
        return redirect(url_for('approvals.approvals', tab='assets'))

    return render_template(
        'approve_asset.html',
        asset=pending_asset,
        original=pending_asset.original,
        asset_fields=ASSET_TYPE_FIELDS.get(pending_asset.asset_type, ()),
        active_page='approvals'
    )

@approvals_bp.route('/approvals/balance/<int:account_id>/<int:riport_id>/approve', methods=['POST'])
@login_required
def approve_balance(account_id, riport_id):
    pending_balance = BankAccountPendingBalance.query.get_or_404((account_id, riport_id))

    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('approvals.approvals', tab='balances'))

    if (current_user.role != 'Admin') and (current_user.id == pending_balance.inspector_1):
        flash('You can not approve your own balance entry!', 'danger')
        return redirect(url_for('approvals.approvals', tab='balances'))

    approved_balance = db.session.get(BankAccountBalance, (account_id, riport_id))
    if approved_balance is None:
        approved_balance = BankAccountBalance(account_id=account_id, riport_id=riport_id)
        db.session.add(approved_balance)

    approved_balance.balance = pending_balance.balance
    approved_balance.state = "Approved"
    approved_balance.inspector_1 = pending_balance.inspector_1
    approved_balance.inspector_2 = current_user.id
    approved_balance.approval_time = datetime.utcnow()

    db.session.delete(pending_balance)
    db.session.commit()

    return redirect(url_for('approvals.approvals', tab='balances'))
