from flask import Blueprint, render_template, redirect, url_for, request, flash
from datetime import datetime, date
from app.extensions import db
from app.models import ManagedAssets, ManagedAssetsPending, Currency
from flask_login import login_required, current_user

ALLOWED_ROLES = ['Admin', 'Approver']

managed_assets_bp = Blueprint('managed_assets', __name__)

@managed_assets_bp.route('/managed-assets')
@login_required
def managed_assets():
    assets = ManagedAssets.query.all()
    return render_template('managed_assets.html', assets=assets, active_page='managed_assets')

@managed_assets_bp.route('/managed-assets/new', methods=['GET', 'POST'])
@login_required
def new_managed_asset():
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('managed_assets.managed_assets'))
    
    if request.method == 'POST':
        date_str = request.form.get('contract_date')
        asset_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
        
        end_date_str = request.form.get('end_date')
        
        status = 'Inactive'
        
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
        if end_date == None:
            status = 'Active'
        elif (end_date >= date.today()):
            status = 'Active'

        new_asset = ManagedAssetsPending(
            asset_name=request.form.get('asset_name'),
            contract_number=request.form.get('contract_number'),
            tax_number=request.form.get('tax_number'),
            contract_date=asset_date,
            end_date=end_date,
            riporting_currency=request.form.get('riporting_currency'),
            status=status,
            state="Pending",
            inspector_1=current_user.id
        )
        db.session.add(new_asset)
        db.session.commit()
        return redirect(url_for('managed_assets.managed_assets'))

    currencies = Currency.query.all()
    return render_template('assets_form.html', asset=None, currencies=currencies, active_page='managed_assets')

@managed_assets_bp.route('/managed-assets/<int:asset_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_managed_assets(asset_id):
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('managed_assets.managed_assets'))
    
    asset = ManagedAssets.query.get_or_404(asset_id)

    if request.method == 'POST':
        date_str = request.form.get('date')
        asset.asset_name = request.form.get('asset_name')
        asset.contract_number = request.form.get('contract_number')
        asset.tax_number = request.form.get('tax_number')
        asset.contract_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else asset.contract_date
        asset.end_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else asset.end_date
        asset.riporting_currency = request.form.get('riporting_currency', type=int)
        asset.status = request.form.get('status')
        asset.state="Pending"
        asset.inspector_1=current_user.id

        db.session.commit()
        return redirect(url_for('managed_assets.managed_assets'))

    currencies = Currency.query.all()
    statuses = ["Active", "Inactive"]
    return render_template('assets_form.html', asset=asset, currencies=currencies, statuses=statuses, active_page='managed_assets')

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
    db.session.delete(asset)
    db.session.commit()
    return redirect(url_for('approvals'))