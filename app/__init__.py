from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

migrate = Migrate()

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    migrate.init_app(app, db)

    # Register blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.main import main_bp
    from app.blueprints.items import items_bp
    from app.blueprints.transfers import transfers_bp
    from app.blueprints.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(items_bp, url_prefix='/items')
    app.register_blueprint(transfers_bp, url_prefix='/transfers')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Register custom Jinja filters
    register_template_filters(app)

    # Create DB and seed if needed
    with app.app_context():
        db.create_all()
        seed_initial_data()

    return app


def register_template_filters(app):
    @app.template_filter('datetime')
    def format_datetime(value, fmt='%Y-%m-%d %H:%M'):
        if value is None:
            return ''
        return value.strftime(fmt)

    @app.template_filter('date')
    def format_date(value, fmt='%Y-%m-%d'):
        if value is None:
            return ''
        return value.strftime(fmt)

    @app.template_filter('status_badge')
    def status_badge(status):
        mapping = {
            'active': 'success',
            'decommissioned': 'secondary',
            'pending_transfer': 'warning',
            'in_transit': 'info',
        }
        return mapping.get(status, 'secondary')


def seed_initial_data():
    """Seed default admin, categories, and a main resource center."""
    from app.models import User, Category, ResourceCenter

    if User.query.filter_by(username='admin').first():
        return

    admin = User(username='admin', email='admin@rescuecenter.local', is_admin=True)
    admin.set_password('admin123')

    categories = [
        Category(name='Electronics', description='Electronic devices and equipment'),
        Category(name='Furniture', description='Tables, chairs, beds, etc.'),
        Category(name='Stationery', description='Office and school supplies'),
        Category(name='Clothing', description='Clothes and textiles'),
        Category(name='Food', description='Non-perishable food items'),
        Category(name='Medical', description='Medical supplies and equipment'),
        Category(name='Kitchen', description='Kitchen utensils and appliances'),
        Category(name='Other', description='Miscellaneous items'),
    ]

    main_center = ResourceCenter(
        name='Main Rescue Center',
        location='City Center',
        contact_person='Admin',
        contact_email='main@rescuecenter.local',
        contact_phone='+1234567890',
    )

    db.session.add(admin)
    db.session.add_all(categories)
    db.session.add(main_center)
    db.session.commit()
    print('✔ Seeded default admin (admin / admin123) and base data.')