#!/usr/bin/env python3
"""
Final Migration Script - Explicit Database Connections
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def main():
    """Run the complete migration"""
    print("🚀 AquaCRM SQLite to Supabase Migration")
    print("=" * 50)
    
    # Explicit database URLs
    sqlite_url = "sqlite:///app.db"
    pooler_url = "postgresql://postgres.urhejrvbaaxnkwcqvhur:2CYHK3RDQWLQTwtx@aws-0-us-east-2.pooler.supabase.com:6543/postgres"
    
    print("🎯 Target: Supabase PostgreSQL (Pooler)")
    
    # Test PostgreSQL connection
    print("\n🔍 Testing Supabase connection...")
    try:
        postgres_engine = create_engine(pooler_url)
        with postgres_engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ PostgreSQL connection successful!")
            print(f"PostgreSQL: {version[:60]}...")
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False
    
    # Test SQLite connection
    print(f"\n📊 Source: SQLite database")
    try:
        sqlite_engine = create_engine(sqlite_url)
        with sqlite_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='table'"))
            table_count = result.scalar()
            print(f"✅ SQLite: {table_count} tables found")
    except Exception as e:
        print(f"❌ SQLite connection failed: {e}")
        return False
    
    # Confirm migration
    response = input("\nProceed with migration? (yes/no): ").lower().strip()
    if response not in ['yes', 'y']:
        print("Migration cancelled.")
        return False
    
    try:
        # Import models after confirming
        from app.models import Client, Quote, QuoteItem, Invoice, InvoiceItem, Payment, EmailLog, Service
        
        # Create backup
        print("\n💾 Creating backup...")
        import shutil
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"app.db.backup_{timestamp}"
        shutil.copy2("app.db", backup_name)
        print(f"✅ Backup created: {backup_name}")
        
        # Start migration
        print("\n🚀 Starting migration...")
        
        # Create sessions
        SqliteSession = sessionmaker(bind=sqlite_engine)
        PostgresSession = sessionmaker(bind=postgres_engine)
        
        sqlite_session = SqliteSession()
        postgres_session = PostgresSession()
        
        # Create tables in PostgreSQL using raw SQL
        print("📋 Creating PostgreSQL tables...")
        
        # Create tables manually to avoid Flask app context issues
        create_tables_sql = """
        -- Create clients table
        CREATE TABLE IF NOT EXISTS client (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(120),
            phone VARCHAR(20),
            address TEXT,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create services table
        CREATE TABLE IF NOT EXISTS service (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            price DECIMAL(10,2)
        );
        
        -- Create quotes table
        CREATE TABLE IF NOT EXISTS quote (
            id SERIAL PRIMARY KEY,
            quote_number VARCHAR(20) UNIQUE NOT NULL,
            client_id INTEGER REFERENCES client(id),
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_expires TIMESTAMP,
            status VARCHAR(20) DEFAULT 'draft',
            notes TEXT,
            total_amount DECIMAL(10,2) DEFAULT 0
        );
        
        -- Create quote_item table
        CREATE TABLE IF NOT EXISTS quote_item (
            id SERIAL PRIMARY KEY,
            quote_id INTEGER REFERENCES quote(id),
            service_id INTEGER REFERENCES service(id),
            description TEXT,
            quantity INTEGER DEFAULT 1,
            unit_price DECIMAL(10,2),
            total_price DECIMAL(10,2)
        );
        
        -- Create invoices table
        CREATE TABLE IF NOT EXISTS invoice (
            id SERIAL PRIMARY KEY,
            invoice_number VARCHAR(20) UNIQUE NOT NULL,
            client_id INTEGER REFERENCES client(id),
            quote_id INTEGER REFERENCES quote(id),
            date_issued TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_due TIMESTAMP,
            status VARCHAR(20) DEFAULT 'pending',
            notes TEXT,
            total_amount DECIMAL(10,2) DEFAULT 0
        );
        
        -- Create invoice_item table
        CREATE TABLE IF NOT EXISTS invoice_item (
            id SERIAL PRIMARY KEY,
            invoice_id INTEGER REFERENCES invoice(id),
            service_id INTEGER REFERENCES service(id),
            description TEXT,
            quantity INTEGER DEFAULT 1,
            unit_price DECIMAL(10,2),
            total_price DECIMAL(10,2)
        );
        
        -- Create payments table
        CREATE TABLE IF NOT EXISTS payment (
            id SERIAL PRIMARY KEY,
            invoice_id INTEGER REFERENCES invoice(id),
            amount DECIMAL(10,2) NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            method VARCHAR(50),
            notes TEXT
        );
        
        -- Create email_log table
        CREATE TABLE IF NOT EXISTS email_log (
            id SERIAL PRIMARY KEY,
            recipient VARCHAR(120) NOT NULL,
            subject VARCHAR(200),
            body TEXT,
            date_sent TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'sent'
        );
        """
        
        with postgres_engine.begin() as conn:
            # Execute each CREATE TABLE statement
            for statement in create_tables_sql.split(';'):
                if statement.strip():
                    conn.execute(text(statement))
        
        print("✅ Tables created")
        
        # Migration order and table mappings
        migrations = [
            ('client', Client, "clients"),
            ('service', Service, "services"),
            ('quote', Quote, "quotes"),
            ('quote_item', QuoteItem, "quote items"),
            ('invoice', Invoice, "invoices"),
            ('invoice_item', InvoiceItem, "invoice items"),
            ('payment', Payment, "payments"),
            ('email_log', EmailLog, "email logs"),
        ]
        
        total_migrated = 0
        
        for table_name, model_class, description in migrations:
            print(f"\n📦 Migrating {description}...")
            
            # Get SQLite data
            records = sqlite_session.query(model_class).all()
            count = len(records)
            
            if count == 0:
                print(f"   No {description} to migrate")
                continue
            
            print(f"   Found {count} {description}")
            
            # Migrate records
            migrated = 0
            for record in records:
                try:
                    # Get record data
                    data = {}
                    for column in model_class.__table__.columns:
                        value = getattr(record, column.name)
                        data[column.name] = value
                    
                    # Create new record in PostgreSQL
                    new_record = model_class(**data)
                    postgres_session.add(new_record)
                    migrated += 1
                    
                    # Batch commit
                    if migrated % 50 == 0:
                        postgres_session.commit()
                
                except Exception as e:
                    print(f"   ⚠️  Error with record {record.id}: {e}")
                    postgres_session.rollback()
                    continue
            
            # Final commit
            try:
                postgres_session.commit()
                print(f"   ✅ Migrated {migrated}/{count} {description}")
                total_migrated += migrated
            except Exception as e:
                print(f"   ❌ Error committing {description}: {e}")
                postgres_session.rollback()
        
        print(f"\n🎉 Migration complete! {total_migrated} records migrated")
        
        # Verify migration
        print("\n🔍 Verifying migration...")
        all_good = True
        
        for table_name, model_class, description in migrations:
            sqlite_count = sqlite_session.query(model_class).count()
            postgres_count = postgres_session.query(model_class).count()
            
            if sqlite_count == postgres_count:
                print(f"   ✅ {description}: {postgres_count} records")
            else:
                print(f"   ❌ {description}: SQLite={sqlite_count}, PostgreSQL={postgres_count}")
                all_good = False
        
        if all_good:
            print("\n🎊 Verification passed! All data migrated successfully.")
            
            # Update .env file
            print("\n📝 Updating .env file...")
            env_content = []
            if os.path.exists('.env'):
                with open('.env', 'r') as f:
                    env_content = f.readlines()
            
            # Remove old DATABASE_URL
            env_content = [line for line in env_content if not line.startswith('DATABASE_URL=')]
            
            # Add new DATABASE_URL
            env_content.append(f'DATABASE_URL={pooler_url}\n')
            
            with open('.env', 'w') as f:
                f.writelines(env_content)
            
            print("✅ .env file updated")
            print("\n🎉 MIGRATION COMPLETED SUCCESSFULLY!")
            print("=" * 50)
            print("✅ All data migrated to Supabase PostgreSQL")
            print("✅ App configured to use Supabase")
            print("✅ .env file updated")
            print()
            print("🚀 Your AquaCRM app is now running on Supabase!")
            print()
            print("Next steps:")
            print("1. Restart your Flask application")
            print("2. Test all functionality")
            print("3. Remove SQLite files when satisfied")
            
            return True
        else:
            print("\n⚠️  Some data may not have migrated correctly.")
            return False
        
        # Close sessions
        sqlite_session.close()
        postgres_session.close()
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ Migration completed successfully!")
        else:
            print("\n❌ Migration failed.")
    except KeyboardInterrupt:
        print("\n\n❌ Migration cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}") 