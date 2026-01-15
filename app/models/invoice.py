from datetime import datetime
from decimal import Decimal
from app import db

class Invoice(db.Model):
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    quote_id = db.Column(db.Integer, db.ForeignKey('quotes.id'))
    invoice_number = db.Column(db.String(20), unique=True, nullable=False)
    date_issued = db.Column(db.Date, default=datetime.utcnow().date)
    due_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='draft')  # draft, sent, paid, overdue
    notes = db.Column(db.Text)
    total = db.Column(db.Numeric(10, 2), default=0.0)
    
    # Relationships
    items = db.relationship('InvoiceItem', backref='invoice', lazy='dynamic', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='invoice', lazy='dynamic')
    email_logs = db.relationship('EmailLog', backref='invoice', lazy='dynamic')
    
    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'
    
    def calculate_total(self):
        """Calculate the total from all line items"""
        from decimal import Decimal
        self.total = sum(item.line_total or Decimal('0') for item in self.items) or Decimal('0')
        return self.total
    
    def calculate_balance(self):
        """Calculate remaining balance after payments"""
        if self.total is None:
            return Decimal('0.0')
        # Convert to Decimal to ensure consistency
        total = Decimal(str(self.total)) if not isinstance(self.total, Decimal) else self.total
        total_paid = sum((Decimal(str(payment.amount)) if not isinstance(payment.amount, Decimal) else payment.amount) for payment in self.payments)
        return total - total_paid


class InvoiceItem(db.Model):
    __tablename__ = 'invoice_items'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    line_total = db.Column(db.Numeric(10, 2))
    
    def __repr__(self):
        return f'<InvoiceItem {self.description}>'
    
    def calculate_line_total(self):
        """Calculate line total from quantity and unit price"""
        from decimal import Decimal
        quantity = self.quantity or Decimal('0')
        unit_price = self.unit_price or Decimal('0')
        self.line_total = quantity * unit_price
        return self.line_total 