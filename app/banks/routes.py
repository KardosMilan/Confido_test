from flask import Blueprint, render_template, redirect, url_for, request, flash
from app.extensions import db
from app.models import Bank
from flask_login import login_required, current_user

ALLOWED_ROLES = ['Admin', 'Approver']

banks_bp = Blueprint('banks', __name__)

@banks_bp.route('/banks')
@login_required
def banks():
    all_banks = Bank.query.order_by(Bank.bank_id.asc()).all()
    return render_template('banks.html', banks=all_banks, active_page='banks')

@banks_bp.route('/banks/new', methods=['GET', 'POST'])
@login_required
def new_bank():
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('banks.banks'))
    
    if request.method == 'POST':
        new_b = Bank(
            bank_id=request.form.get('bank_id', type=int),
            bank_name=request.form.get('bank_name'),
            region=request.form.get('region')
        )
        db.session.add(new_b)
        db.session.commit()
        return redirect(url_for('banks.banks'))

    return render_template('banks_form.html', bank=None, active_page='banks')

@banks_bp.route('/banks/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_bank(id):
    if current_user.role not in ALLOWED_ROLES:
            flash('No permission granted!', 'danger')
            return redirect(url_for('banks.banks'))
    
    bank = Bank.query.get_or_404(id)

    if request.method == 'POST':
        bank.bank_id = request.form.get('bank_id', type=int)
        bank.bank_name = request.form.get('bank_name')
        bank.region = request.form.get('region')

        db.session.commit()
        return redirect(url_for('banks.banks'))

    return render_template('banks_form.html', bank=bank, active_page='banks')

@banks_bp.route('/banks/<int:id>/delete', methods=['POST'])
@login_required
def delete_bank(id):
    if current_user.role not in ALLOWED_ROLES:
            flash('No permission granted!', 'danger')
            return redirect(url_for('banks.banks'))
    
    if current_user.role in ALLOWED_ROLES:
        bank = Bank.query.get_or_404(id)
        db.session.delete(bank)
        db.session.commit()
        return redirect(url_for('banks.banks'))