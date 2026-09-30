from datetime import datetime
from decimal import Decimal, InvalidOperation
from flask import Blueprint, render_template, redirect, url_for, request, flash
from pydantic import ValidationError
from app.extensions import db
from app.identifiers import SecurityIdentifier, first_error
from app.models import ManagedAssets, ManagedAssetsPending, Currency, AssetType, ASSET_TYPE_FIELDS, ASSET_FIELDS, copy_fields
from flask_login import login_required, current_user

ALLOWED_ROLES = ['Admin', 'Approver']
OPTIONAL_FIELDS = ('isin', 'nominal_value', 'price_decimals')

managed_assets_bp = Blueprint('managed_assets', __name__)


def field_types():
    return {
        field: [asset_type for asset_type, fields in ASSET_TYPE_FIELDS.items() if field in fields]
        for field in OPTIONAL_FIELDS
    }


def validate_asset_form(form):
    asset_type = form.get('asset_type')
    if asset_type not in ASSET_TYPE_FIELDS:
        return None, 'Please select a valid asset type!'
    fields = ASSET_TYPE_FIELDS[asset_type]

    values = {
        'asset_type': asset_type,
        'asset_name': (form.get('asset_name') or '').strip(),
        'currency_id': form.get('currency_id', type=int),
        'isin': None,
        'nominal_value': None,
        'price_decimals': None,
    }

    if not values['asset_name']:
        return None, 'Asset name is required!'
    if values['currency_id'] is None or db.session.get(Currency, values['currency_id']) is None:
        return None, 'Please select a valid currency!'

    if 'isin' in fields:
        try:
            values['isin'] = SecurityIdentifier(isin=form.get('isin')).isin
        except ValidationError as exc:
            return None, first_error(exc)

    if 'nominal_value' in fields:
        try:
            nominal_value = Decimal((form.get('nominal_value') or '').strip().replace(' ', ''))
        except InvalidOperation:
            return None, 'Nominal value must be a number!'
        if not nominal_value.is_finite() or nominal_value <= 0:
            return None, 'Nominal value must be greater than zero!'
        if nominal_value != nominal_value.quantize(Decimal('0.01')):
            return None, 'Nominal value can have at most 2 decimal places!'
        values['nominal_value'] = nominal_value

    if 'price_decimals' in fields:
        values['price_decimals'] = form.get('price_decimals', type=int)
        if values['price_decimals'] is None or not 0 <= values['price_decimals'] <= 10:
            return None, 'Price quotation decimals must be a whole number between 0 and 10!'

    return values, None


def fill_asset(target, values):
    for key, value in values.items():
        setattr(target, key, value)
    target.state = "Pending"
    target.inspector_1 = current_user.id
    target.approval_time = datetime.utcnow()


def draft_from_form(form):
    return ManagedAssetsPending(
        asset_type=form.get('asset_type'),
        asset_name=form.get('asset_name'),
        currency_id=form.get('currency_id', type=int),
        isin=form.get('isin'),
        nominal_value=form.get('nominal_value'),
        price_decimals=form.get('price_decimals'),
    )


def render_asset_form(asset, title, form_action, cancel_url, active_page):
    return render_template(
        'assets_form.html',
        asset=asset,
        title=title,
        form_action=form_action,
        cancel_url=cancel_url,
        asset_types=[t.value for t in AssetType],
        field_types=field_types(),
        currencies=Currency.query.all(),
        active_page=active_page
    )


@managed_assets_bp.route('/managed-assets')
@login_required
def managed_assets():
    assets = ManagedAssets.query.order_by(ManagedAssets.asset_name).all()
    return render_template('managed_assets.html', assets=assets, active_page='managed_assets')

@managed_assets_bp.route('/managed-assets/new', methods=['GET', 'POST'])
@login_required
def new_managed_asset():
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('managed_assets.managed_assets'))

    title = 'New Managed Asset'
    form_action = url_for('managed_assets.new_managed_asset')
    cancel_url = url_for('managed_assets.managed_assets')

    if request.method == 'POST':
        values, error = validate_asset_form(request.form)
        if error:
            flash(error, 'danger')
            return render_asset_form(draft_from_form(request.form), title, form_action, cancel_url, 'managed_assets')

        new_asset = ManagedAssetsPending()
        fill_asset(new_asset, values)
        db.session.add(new_asset)
        db.session.commit()
        flash('Asset saved and sent for approval.', 'success')
        return redirect(url_for('managed_assets.managed_assets'))

    return render_asset_form(None, title, form_action, cancel_url, 'managed_assets')

@managed_assets_bp.route('/managed-assets/<int:asset_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_managed_assets(asset_id):
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('managed_assets.managed_assets'))

    asset = ManagedAssets.query.get_or_404(asset_id)
    change = asset.pending_changes[0] if asset.pending_changes else None
    title = 'Edit Managed Asset'
    form_action = url_for('managed_assets.edit_managed_assets', asset_id=asset_id)
    cancel_url = url_for('managed_assets.managed_assets')

    if request.method == 'POST':
        values, error = validate_asset_form(request.form)
        if error:
            flash(error, 'danger')
            return render_asset_form(draft_from_form(request.form), title, form_action, cancel_url, 'managed_assets')

        if change is None:
            change = ManagedAssetsPending(original=asset)
            copy_fields(asset, change, ASSET_FIELDS)
            db.session.add(change)

        fill_asset(change, values)
        asset.state = "Pending"

        db.session.commit()
        flash('Changes saved and sent for approval.', 'success')
        return redirect(url_for('managed_assets.managed_assets'))

    return render_asset_form(change or asset, title, form_action, cancel_url, 'managed_assets')

@managed_assets_bp.route('/managed-assets-pending/<int:asset_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_managed_assets_pending(asset_id):
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('approvals.approvals', tab='assets'))

    asset = ManagedAssetsPending.query.get_or_404(asset_id)
    title = 'Edit Pending Asset'
    form_action = url_for('managed_assets.edit_managed_assets_pending', asset_id=asset_id)
    cancel_url = url_for('approvals.approve_asset', asset_id=asset_id)

    if request.method == 'POST':
        values, error = validate_asset_form(request.form)
        if error:
            flash(error, 'danger')
            return render_asset_form(draft_from_form(request.form), title, form_action, cancel_url, 'approvals')

        fill_asset(asset, values)
        db.session.commit()
        return redirect(url_for('approvals.approvals', tab='assets'))

    return render_asset_form(asset, title, form_action, cancel_url, 'approvals')

@managed_assets_bp.route('/managed-assets/<int:asset_id>/delete', methods=['POST'])
@login_required
def delete_managed_assets(asset_id):
    asset = ManagedAssets.query.get_or_404(asset_id)
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('managed_assets.managed_assets'))

    db.session.delete(asset)
    db.session.commit()
    return redirect(url_for('managed_assets.managed_assets'))

@managed_assets_bp.route('/managed-assets-pending/<int:asset_id>/delete', methods=['POST'])
@login_required
def delete_managed_assets_pending(asset_id):
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('managed_assets.managed_assets'))

    asset = ManagedAssetsPending.query.get_or_404(asset_id)
    if asset.original:
        asset.original.state = "Approved"
    db.session.delete(asset)
    db.session.commit()
    return redirect(url_for('approvals.approvals', tab='assets'))
