from flask import Blueprint, render_template
from flask_login import login_required

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=["POST", "GET"])
@login_required
def index():
    return render_template("index.html", active_page='index')

@main_bp.route('/reports')
@login_required
def reports():
    return render_template('reports.html', active_page='reports')