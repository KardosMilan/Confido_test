from flask import Flask, session
from flask_scss import Scss
from app.config import Config
from app.extensions import db, oauth, login_manager
from app.models import (
    User,
    ManagedTrusts,
    ManagedTrustsPending,
    BankAccount,
    BankAccountPending,
)
from app.formatting import format_amount
from app.identifiers import format_iban, format_pfj, format_isin
from datetime import date
from flask_apscheduler import APScheduler

STATUS_MODELS = (
    ManagedTrusts,
    ManagedTrustsPending,
    BankAccount,
    BankAccountPending,
)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    oauth.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = None

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    @app.before_request
    def make_session_permanent():
        session.permanent = True
        session.modified = True

    app.add_template_filter(format_amount, 'amount')
    app.add_template_filter(format_iban, 'iban')
    app.add_template_filter(format_pfj, 'pfj')
    app.add_template_filter(format_isin, 'isin')

    oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

    Scss(app)

    scheduler = APScheduler()

    def daily_status_check():
        with app.app_context():
            today = date.today()
            for model in STATUS_MODELS:
                expired_records = model.query.filter(
                    model.status == 'Active',
                    model.end_date < today
                ).all()

                for record in expired_records:
                    record.status = 'Inactive'

            db.session.commit()

    class Config:
        SCHEDULER_API_ENABLED = True

    app.config.from_object(Config())
    scheduler.init_app(app)

    scheduler.add_job(
        id='daily_status_deactivation',
        func=daily_status_check,
        trigger='cron',
        hour=0,
        minute=5
    )

    scheduler.start()

    from app.main.routes import main_bp
    from app.bank_accounts.routes import bank_accounts_bp
    from app.managed_trusts.routes import managed_trusts_bp
    from app.approvals.routes import approvals_bp
    from app.auth.routes import auth_bp
    from app.banks.routes import banks_bp
    from app.users.routes import users_bp
    from app.managed_assets.routes import managed_assets_bp
    from app.data_entry.routes import data_entry_bp
    from app.reports.routes import reports_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(bank_accounts_bp)
    app.register_blueprint(managed_trusts_bp)
    app.register_blueprint(managed_assets_bp)
    app.register_blueprint(approvals_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(banks_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(data_entry_bp)
    app.register_blueprint(reports_bp)

    with app.app_context():
        db.create_all()
        from app.models import seed_banks
        from app.models import seed_currencies
        seed_banks()
        seed_currencies()

    return app