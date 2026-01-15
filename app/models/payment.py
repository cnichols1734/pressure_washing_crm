from datetime import datetime
from decimal import Decimal
from app import db

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow().date)
    method = db.Column(db.String(50))  # Credit Card, Check, etc.
    reference = db.Column(db.String(100))  # Reference number for payment
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Payment ${self.amount} for Invoice {self.invoice_id}>' 