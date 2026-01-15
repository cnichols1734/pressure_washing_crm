#!/usr/bin/env python3
"""
Test script to verify invoice-quote relationship
"""

from app import create_app, db
from app.models import Quote, Invoice, Client
from sqlalchemy.orm import joinedload

def test_invoice_quote_relationship():
    app = create_app()
    with app.app_context():
        print("Current state of database:")
        print("=" * 50)
        
        # Check all quotes
        quotes = Quote.query.all()
        print(f"Total quotes: {len(quotes)}")
        for quote in quotes:
            print(f"  Quote {quote.id}: {quote.quote_number}")
            print(f"    Status: {quote.status}")
            print(f"    Invoice: {quote.invoice}")
            print()
        
        # Check all invoices
        invoices = Invoice.query.all()
        print(f"Total invoices: {len(invoices)}")
        for invoice in invoices:
            print(f"  Invoice {invoice.id}: {invoice.invoice_number}")
            print(f"    Quote ID: {invoice.quote_id}")
            print(f"    Quote: {invoice.quote}")
            print()
        
        # Test the relationship explicitly
        print("Testing relationship:")
        print("=" * 50)
        for invoice in invoices:
            if invoice.quote_id:
                quote = Quote.query.get(invoice.quote_id)
                print(f"Invoice {invoice.invoice_number} has quote_id={invoice.quote_id}")
                print(f"  Quote from ID: {quote}")
                print(f"  Quote's invoice: {quote.invoice if quote else 'N/A'}")
                print(f"  Relationship works: {quote.invoice == invoice if quote else False}")
            else:
                print(f"Invoice {invoice.invoice_number} has no quote_id")

if __name__ == "__main__":
    test_invoice_quote_relationship() 