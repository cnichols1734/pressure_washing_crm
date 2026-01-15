from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_login import LoginManager, login_required
from config import Config

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
login = LoginManager()
login.login_view = 'auth.login'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    login.init_app(app)

    # Register blueprints here
    from app.routes.clients import bp as clients_bp, api_bp as clients_api_bp
    from app.routes.services import bp as services_bp
    from app.routes.quotes import bp as quotes_bp, api_bp as quotes_api_bp
    from app.routes.invoices import bp as invoices_bp, api_bp as invoices_api_bp
    from app.routes.payments import bp as payments_bp, api_bp as payments_api_bp
    from app.routes.emails import bp as emails_bp
    from app.routes.auth import bp as auth_bp
    
    app.register_blueprint(clients_bp)
    app.register_blueprint(clients_api_bp)
    app.register_blueprint(services_bp)
    app.register_blueprint(quotes_bp)
    app.register_blueprint(quotes_api_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(invoices_api_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(payments_api_bp)
    app.register_blueprint(emails_bp)
    app.register_blueprint(auth_bp)

    @app.route('/')
    @login_required
    def index():
        from app.models import Client, Quote, Invoice, Payment
        from datetime import datetime, timedelta
        
        # Get statistics for dashboard
        stats = {
            'total_clients': Client.query.count(),
            'active_quotes': Quote.query.filter(Quote.status.in_(['draft', 'sent'])).count(),
            'outstanding_amount': sum(inv.calculate_balance() for inv in Invoice.query.all() if inv.calculate_balance() > 0),
            'monthly_revenue': sum(p.amount for p in Payment.query.filter(
                Payment.date >= datetime.now().replace(day=1)
            ))
        }
        
        # Get recent activity
        recent_activity = []
        
        # Recent quotes
        recent_quotes = Quote.query.order_by(Quote.date_created.desc()).limit(5).all()
        for quote in recent_quotes:
            recent_activity.append({
                'type': 'quote',
                'description': f'Quote {quote.quote_number} created for {quote.client.name}',
                'timestamp': quote.date_created,
                'link': f'/quotes/{quote.id}'
            })
        
        # Recent invoices
        recent_invoices = Invoice.query.order_by(Invoice.date_issued.desc()).limit(5).all()
        for invoice in recent_invoices:
            recent_activity.append({
                'type': 'invoice',
                'description': f'Invoice {invoice.invoice_number} issued to {invoice.client.name}',
                'timestamp': invoice.date_issued,
                'link': f'/invoices/{invoice.id}'
            })
        
        # Recent payments
        recent_payments = Payment.query.order_by(Payment.date.desc()).limit(5).all()
        for payment in recent_payments:
            # Only add payments that have valid invoices (avoid orphaned payments)
            if payment.invoice:
                recent_activity.append({
                    'type': 'payment',
                    'description': f'Payment of ${payment.amount:.2f} received for Invoice {payment.invoice.invoice_number}',
                    'timestamp': payment.date,
                    'link': f'/invoices/{payment.invoice_id}'
                })
        
        # Sort activities by timestamp
        recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
        recent_activity = recent_activity[:10]  # Keep only the 10 most recent activities
        
        return render_template('dashboard.html', stats=stats, recent_activity=recent_activity)

    @app.context_processor
    def inject_now():
        from datetime import datetime
        return {'now': datetime.utcnow()}

    return app

from app import models 