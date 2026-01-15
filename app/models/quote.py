from datetime import datetime
from decimal import Decimal
from app import db

class Quote(db.Model):
    __tablename__ = 'quotes'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    quote_number = db.Column(db.String(20), unique=True, nullable=False)
    date_created = db.Column(db.Date, default=datetime.utcnow().date)
    valid_until = db.Column(db.Date)
    status = db.Column(db.String(20), default='draft')  # draft, sent, accepted, rejected, expired
    notes = db.Column(db.Text)
    total = db.Column(db.Numeric(10, 2), default=0.0)
    
    # Relationships
    items = db.relationship('QuoteItem', backref='quote', lazy='dynamic', cascade='all, delete-orphan')
    invoice = db.relationship('Invoice', backref='quote', uselist=False)
    email_logs = db.relationship('EmailLog', backref='quote', lazy='dynamic')
    
    def __repr__(self):
        return f'<Quote {self.quote_number}>'
    
    def calculate_total(self):
        """Calculate the total from all line items"""
        from decimal import Decimal
        self.total = sum(item.line_total or Decimal('0') for item in self.items) or Decimal('0')
        return self.total


class QuoteItem(db.Model):
    __tablename__ = 'quote_items'
    
    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('quotes.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    line_total = db.Column(db.Numeric(10, 2))
    
    def __repr__(self):
        return f'<QuoteItem {self.description}>'
    
    def calculate_line_total(self):
        """Calculate line total from quantity and unit price"""
        from decimal import Decimal
        quantity = self.quantity or Decimal('0')
        unit_price = self.unit_price or Decimal('0')
        self.line_total = quantity * unit_price
        return self.line_total 