#!/usr/bin/env python3
"""
Test script to verify migration setup
"""

import os
import sys
from sqlalchemy import create_engine, text
import getpass

def test_sqlite_connection():
    """Test SQLite connection"""
    try:
        from app import create_app
        app = create_app()
        sqlite_uri = app.config['SQLALCHEMY_DATABASE_URI']
        
        engine = create_engine(sqlite_uri)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='table'"))
            table_count = result.scalar()
            print(f"✓ SQLite connection successful - Found {table_count} tables")
            
            # Get record counts
            from app.models import Client, Quote, Invoice, Payment
            with app.app_context():
                from app import db
                print(f"  - Clients: {Client.query.count()}")
                print(f"  - Quotes: {Quote.query.count()}")
                print(f"  - Invoices: {Invoice.query.count()}")
                print(f"  - Payments: {Payment.query.count()}")
        
        return True
    except Exception as e:
        print(f"✗ SQLite connection failed: {e}")
        return False

def test_postgresql_connection():
    """Test PostgreSQL connection"""
    try:
        # Get the full database URL from environment or prompt user
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            print("Please provide your Supabase database connection details:")
            print("You can find these in your Supabase dashboard under Settings > Database")
            
            host = input("Database Host (e.g., db.xxxxxxxxxxxxx.supabase.co): ").strip()
            if not host:
                print("Error: Host is required")
                return False
            
            password = os.environ.get('SUPABASE_PASSWORD')
            if not password:
                password = getpass.getpass("Database Password: ")
            
            database_url = f"postgresql://postgres:{password}@{host}:5432/postgres"
        
        engine = create_engine(database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✓ PostgreSQL connection successful")
            print(f"  Version: {version[:80]}...")
        
        return True
    except Exception as e:
        print(f"✗ PostgreSQL connection failed: {e}")
        return False

def test_imports():
    """Test that all required modules can be imported"""
    try:
        import psycopg2
        print(f"✓ psycopg2 version: {psycopg2.__version__}")
        
        from app import create_app, db
        from app.models import Client, Quote, QuoteItem, Invoice, InvoiceItem, Payment, EmailLog, Service
        print("✓ All Flask models imported successfully")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Migration Setup Test")
    print("=" * 30)
    
    all_tests_passed = True
    
    print("\n1. Testing imports...")
    if not test_imports():
        all_tests_passed = False
    
    print("\n2. Testing SQLite connection...")
    if not test_sqlite_connection():
        all_tests_passed = False
    
    print("\n3. Testing PostgreSQL connection...")
    if not test_postgresql_connection():
        all_tests_passed = False
    
    print("\n" + "=" * 30)
    if all_tests_passed:
        print("✅ All tests passed! Ready for migration.")
        print("\nTo run the migration:")
        print("python migrate_to_supabase.py")
    else:
        print("❌ Some tests failed. Please fix the issues before migrating.")

if __name__ == "__main__":
    main() 