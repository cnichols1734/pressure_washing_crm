#!/usr/bin/env python3
"""
Script to clear all business data while preserving user accounts
"""

from app import create_app, db
from app.models import Client, Quote, QuoteItem, Invoice, InvoiceItem, EmailLog, Payment
from sqlalchemy import text

def clear_business_data():
    app = create_app()
    with app.app_context():
        print("Starting data cleanup...")
        
        # Get counts before deletion
        email_count = EmailLog.query.count()
        payment_count = Payment.query.count()
        invoice_item_count = InvoiceItem.query.count()
        quote_item_count = QuoteItem.query.count()
        invoice_count = Invoice.query.count()
        quote_count = Quote.query.count()
        client_count = Client.query.count()
        
        print(f"Records to delete:")
        print(f"  - EmailLog: {email_count}")
        print(f"  - Payment: {payment_count}")
        print(f"  - InvoiceItem: {invoice_item_count}")
        print(f"  - QuoteItem: {quote_item_count}")
        print(f"  - Invoice: {invoice_count}")
        print(f"  - Quote: {quote_count}")
        print(f"  - Client: {client_count}")
        
        # Delete in correct order to avoid foreign key constraints
        print("\nDeleting records...")
        
        # 1. Delete EmailLog first (references quotes and invoices)
        deleted = EmailLog.query.delete()
        print(f"Deleted {deleted} EmailLog records")
        
        # 2. Delete Payment (references invoices)
        deleted = Payment.query.delete()
        print(f"Deleted {deleted} Payment records")
        
        # 3. Delete InvoiceItem (references invoices)
        deleted = InvoiceItem.query.delete()
        print(f"Deleted {deleted} InvoiceItem records")
        
        # 4. Delete QuoteItem (references quotes)  
        deleted = QuoteItem.query.delete()
        print(f"Deleted {deleted} QuoteItem records")
        
        # 5. Delete Invoice (references quotes and clients)
        deleted = Invoice.query.delete()
        print(f"Deleted {deleted} Invoice records")
        
        # 6. Delete Quote (references clients)
        deleted = Quote.query.delete()
        print(f"Deleted {deleted} Quote records")
        
        # 7. Delete Client (referenced by quotes and invoices)
        deleted = Client.query.delete()
        print(f"Deleted {deleted} Client records")
        
        # Reset auto-increment counters for SQLite
        print("\nResetting auto-increment counters...")
        db.session.execute(text("DELETE FROM sqlite_sequence WHERE name IN ('clients', 'quotes', 'quote_items', 'invoices', 'invoice_items', 'email_logs', 'payments')"))
        
        # Commit all changes
        db.session.commit()
        
        print("\n✅ Data cleanup completed successfully!")
        print("User accounts have been preserved - you can still login.")
        print("All business data (clients, quotes, invoices, payments, emails) has been cleared.")
        
        # Verify cleanup
        print("\nVerifying cleanup:")
        print(f"  - EmailLog: {EmailLog.query.count()}")
        print(f"  - Payment: {Payment.query.count()}")
        print(f"  - InvoiceItem: {InvoiceItem.query.count()}")
        print(f"  - QuoteItem: {QuoteItem.query.count()}")
        print(f"  - Invoice: {Invoice.query.count()}")
        print(f"  - Quote: {Quote.query.count()}")
        print(f"  - Client: {Client.query.count()}")

if __name__ == "__main__":
    clear_business_data() 