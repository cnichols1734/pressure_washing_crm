#!/usr/bin/env python3
"""
Test script to simulate invoice creation from quote workflow
"""

from app import create_app, db
from app.models import Quote, Invoice, InvoiceItem
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import joinedload

def test_invoice_creation():
    app = create_app()
    with app.app_context():
        # Find a quote that doesn't have an invoice yet
        quote = Quote.query.filter(~Quote.id.in_(
            db.session.query(Invoice.quote_id).filter(Invoice.quote_id.isnot(None))
        )).first()
        
        if not quote:
            print("No quotes available without invoices")
            return
        
        print(f"Testing with Quote {quote.id}: {quote.quote_number}")
        print(f"Quote status: {quote.status}")
        print(f"Quote has invoice before: {quote.invoice}")
        
        # Simulate invoice creation
        year = datetime.now().year
        last_invoice = Invoice.query.filter(Invoice.invoice_number.like(f'INV-{year}-%')).order_by(Invoice.id.desc()).first()
        if last_invoice:
            last_number = int(last_invoice.invoice_number.split('-')[-1])
            invoice_number = f'INV-{year}-{last_number + 1:03d}'
        else:
            invoice_number = f'INV-{year}-001'
        
        # Create invoice
        invoice = Invoice(
            client_id=quote.client_id,
            quote_id=quote.id,
            invoice_number=invoice_number,
            date_issued=datetime.now().date(),
            due_date=datetime.now().date() + timedelta(days=30),
            status='draft',
            notes=quote.notes
        )
        db.session.add(invoice)
        db.session.flush()
        
        print(f"Created invoice {invoice.id} with quote_id: {invoice.quote_id}")
        
        # Copy quote items to invoice items
        for q_item in quote.items:
            item = InvoiceItem(
                invoice_id=invoice.id,
                description=q_item.description,
                quantity=q_item.quantity,
                unit_price=q_item.unit_price,
                line_total=q_item.line_total
            )
            db.session.add(item)
        
        # Calculate total
        invoice.calculate_total()
        
        # Commit changes
        db.session.commit()
        db.session.flush()
        
        print(f"Invoice committed with total: {invoice.total}")
        
        # Test the relationship after commit
        quote_fresh = Quote.query.get(quote.id)
        print(f"Quote has invoice after (fresh query): {quote_fresh.invoice}")
        print(f"Invoice number: {quote_fresh.invoice.invoice_number if quote_fresh.invoice else 'None'}")
        
        # Test with joinedload
        quote_joined = Quote.query.options(joinedload(Quote.invoice)).get(quote.id)
        print(f"Quote has invoice after (joinedload): {quote_joined.invoice}")
        
        return quote.id, invoice.id

if __name__ == "__main__":
    test_invoice_creation() 