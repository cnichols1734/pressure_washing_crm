from datetime import datetime
from app import db

class EmailLog(db.Model):
    __tablename__ = 'email_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    quote_id = db.Column(db.Integer, db.ForeignKey('quotes.id'))
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'))
    email_type = db.Column(db.String(20))  # quote, invoice
    subject = db.Column(db.String(200))
    body = db.Column(db.Text)
    recipient = db.Column(db.String(100))
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<EmailLog {self.email_type} to {self.recipient}>' 