import re
from flask import Blueprint, render_template, redirect, url_for, request, flash
from app.extensions import db
from app.models import Bank
from flask_login import login_required, current_user

ALLOWED_ROLES = ['Admin', 'Approver']

banks_bp = Blueprint('banks', __name__)


def parse_giro_codes(value, bank_id=None):
    codes = [code for code in re.split(r'[\s,;]+', value or '') if code]
    invalid = [code for code in codes if not re.fullmatch(r'\d{3}', code)]
    if invalid:
        return None, 'GIRO codes must be 3-digit numbers separated by commas!'
    if len(set(codes)) != len(codes):
        return None, 'A GIRO code can only be listed once!'

    for bank in Bank.query.filter(Bank.giro_codes.isnot(None)).all():
        if bank.bank_id == bank_id:
            continue
        taken = set(bank.giro_code_list) & set(codes)
        if taken:
            return None, f'GIRO code {sorted(taken)[0]} already belongs to {bank.bank_name}!'

    return ','.join(codes) or None, None


def render_bank_form(bank, title, form_action):
    return render_template(
        'banks_form.html',
        bank=bank,
        title=title,
        form_action=form_action,
        data_tab='banks',
        active_page='data'
    )


@banks_bp.route('/data')
@login_required
def data():
    return redirect(url_for('banks.banks'))

@banks_bp.route('/banks')
@login_required
def banks():
    all_banks = Bank.query.order_by(Bank.bank_id.asc()).all()
    return render_template('banks.html', banks=all_banks, data_tab='banks', active_page='data')

@banks_bp.route('/banks/new', methods=['GET', 'POST'])
@login_required
def new_bank():
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('banks.banks'))

    title = 'New Bank'
    form_action = url_for('banks.new_bank')

    if request.method == 'POST':
        giro_codes, error = parse_giro_codes(request.form.get('giro_codes'))
        draft = Bank(
            bank_name=request.form.get('bank_name'),
            region=request.form.get('region'),
            giro_codes=giro_codes if not error else request.form.get('giro_codes'),
        )
        if error:
            flash(error, 'danger')
            return render_bank_form(draft, title, form_action)

        db.session.add(draft)
        db.session.commit()
        return redirect(url_for('banks.banks'))

    return render_bank_form(None, title, form_action)

@banks_bp.route('/banks/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_bank(id):
    if current_user.role not in ALLOWED_ROLES:
            flash('No permission granted!', 'danger')
            return redirect(url_for('banks.banks'))

    bank = Bank.query.get_or_404(id)
    title = 'Edit Bank'
    form_action = url_for('banks.edit_bank', id=id)

    if request.method == 'POST':
        giro_codes, error = parse_giro_codes(request.form.get('giro_codes'), bank_id=id)
        if error:
            flash(error, 'danger')
            draft = Bank(
                bank_name=request.form.get('bank_name'),
                region=request.form.get('region'),
                giro_codes=request.form.get('giro_codes'),
            )
            return render_bank_form(draft, title, form_action)

        bank.bank_name = request.form.get('bank_name')
        bank.region = request.form.get('region')
        bank.giro_codes = giro_codes

        db.session.commit()
        return redirect(url_for('banks.banks'))

    return render_bank_form(bank, title, form_action)

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
