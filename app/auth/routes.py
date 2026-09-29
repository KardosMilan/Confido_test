from flask import Blueprint, render_template, redirect, url_for, session
from flask_login import login_user, logout_user, login_required,  current_user
from app.extensions import db, oauth
from app.models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    return render_template('login.html')

@auth_bp.route('/login/google')
def google_login():
    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route('/auth/callback')
def google_callback():
    token = oauth.google.authorize_access_token()
    user_info = token.get('userinfo')

    if not user_info:
        return "Sikertelen Google autentikáció", 400

    google_id = user_info['sub']
    email = user_info['email']
    name = user_info.get('name')
    picture = user_info.get('picture')

    user = User.query.filter_by(email=email).first()

    if not user:
        user = User(
            google_id=google_id,
            email=email,
            name=name,
            role="User",
            picture=picture
        )
        db.session.add(user)
        db.session.commit()
    else:
        user.google_id = google_id
        user.name = name
        user.picture = picture
        db.session.commit()

    session.permanent = True
    login_user(user, remember=False)

    return redirect(url_for('main.index'))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))