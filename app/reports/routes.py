from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Report, ManagedTrusts

ALLOWED_ROLES = ['Admin', 'Approver']
REPORT_FIELDS = ('report_name', 'trust_id', 'report_date', 'description')

reports_bp = Blueprint('reports', __name__)


def parse_date(value):
    try:
        return datetime.strptime(value or '', '%Y-%m-%d').date()
    except ValueError:
        return None


def validate_report_form(form):
    values = {
        'report_name': (form.get('report_name') or '').strip(),
        'trust_id': form.get('trust_id', type=int),
        'report_date': parse_date(form.get('report_date')),
        'description': (form.get('description') or '').strip() or None,
    }

    if not values['report_name']:
        return values, 'Report name is required!'
    if values['report_date'] is None:
        return values, 'Please select a valid report date!'
    if values['trust_id'] is not None and db.session.get(ManagedTrusts, values['trust_id']) is None:
        return values, 'Please select a valid trust!'

    return values, None


def render_report_form(report, title, form_action):
    return render_template(
        'report_form.html',
        report=report,
        title=title,
        form_action=form_action,
        trusts=ManagedTrusts.query.order_by(ManagedTrusts.trust_name).all(),
        active_page='reports'
    )


@reports_bp.route('/reports')
@login_required
def reports():
    reports = Report.query.order_by(Report.report_date.desc(), Report.report_name).all()
    return render_template('reports.html', reports=reports, active_page='reports')

@reports_bp.route('/reports/new', methods=['GET', 'POST'])
@login_required
def new_report():
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('reports.reports'))

    title = 'New Report'
    form_action = url_for('reports.new_report')

    if request.method == 'POST':
        values, error = validate_report_form(request.form)
        if error:
            flash(error, 'danger')
            return render_report_form(Report(**values), title, form_action)

        report = Report(**values, created_by=current_user.id, updated_by=current_user.id)
        db.session.add(report)
        db.session.commit()
        flash('Report saved.', 'success')
        return redirect(url_for('reports.reports'))

    return render_report_form(None, title, form_action)

@reports_bp.route('/reports/<int:report_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_report(report_id):
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('reports.reports'))

    report = Report.query.get_or_404(report_id)
    title = 'Edit Report'
    form_action = url_for('reports.edit_report', report_id=report_id)

    if request.method == 'POST':
        values, error = validate_report_form(request.form)
        if error:
            flash(error, 'danger')
            return render_report_form(Report(**values), title, form_action)

        for field in REPORT_FIELDS:
            setattr(report, field, values[field])
        report.updated_by = current_user.id
        report.updated_at = datetime.utcnow()

        db.session.commit()
        flash('Report updated.', 'success')
        return redirect(url_for('reports.reports'))

    return render_report_form(report, title, form_action)

@reports_bp.route('/reports/<int:report_id>/delete', methods=['POST'])
@login_required
def delete_report(report_id):
    if current_user.role not in ALLOWED_ROLES:
        flash('No permission granted!', 'danger')
        return redirect(url_for('reports.reports'))

    report = Report.query.get_or_404(report_id)
    db.session.delete(report)
    db.session.commit()
    return redirect(url_for('reports.reports'))
