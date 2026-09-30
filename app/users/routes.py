import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import User

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

users_bp = Blueprint('users', __name__)

@users_bp.route('/users')
@login_required
def list_users():
    users = User.query.all()
    return render_template('users.html', users=users, active_page='settings')

@users_bp.route('/users/<int:user_id>/update-role', methods=['POST'])
@login_required
def update_role(user_id):
    if current_user.role != 'Admin':
        return jsonify({'error': 'No access!'}), 403
    
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    
    if new_role:
        user.role = new_role
        db.session.commit()
        
    return redirect(url_for('users.list_users'))

@users_bp.route('/users/make-admin', methods=['POST'])
@login_required
def make_admin():
    data = request.get_json()
    password = data.get('password') if data else None
    
    if password == ADMIN_PASSWORD:
        current_user.role = 'Admin'
        db.session.commit()
        return jsonify({'success': True, 'message': 'Admin rights granted!'})
    else:
        return jsonify({'success': False, 'message': 'Incorrect admin password!'}), 400

@users_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    data = request.get_json()
    password = data.get('password') if data else None

    if password != ADMIN_PASSWORD:
        return jsonify({'success': False, 'message': 'Incorrect admin password!'}), 400

    user_to_delete = User.query.get_or_404(user_id)

    if user_to_delete.id == current_user.id:
        return jsonify({'success': False, 'message': 'You cannot delete your own account!'}), 400

    db.session.delete(user_to_delete)
    db.session.commit()

    return jsonify({
        'success': True, 
        'message': f'User {user_to_delete.name or user_to_delete.email} has been deleted.'
    })