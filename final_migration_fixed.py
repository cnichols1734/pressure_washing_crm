#!/usr/bin/env python3
"""
Final Migration Script - Fixed Engine Separation
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app import create_app, db
from app.models import Client, Quote, QuoteItem, Invoice, InvoiceItem, Payment, EmailLog, Service

def main():
    """Run the complete migration"""
    print("🚀 AquaCRM SQLite to Supabase Migration")
    print("=" * 50)
    
    # Use the working pooler URL
    pooler_url = "postgresql://postgres.urhejrvbaaxnkwcqvhur:2CYHK3RDQWLQTwtx@aws-0-us-east-2.pooler.supabase.com:6543/postgres"
    
    print("🎯 Target: Supabase PostgreSQL (Pooler)")
    
    # Test PostgreSQL connection first
    print("\n🔍 Testing Supabase connection...")
    try:
        test_engine = create_engine(pooler_url)
        with test_engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ PostgreSQL connection successful!")
            print(f"PostgreSQL: {version[:60]}...")
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False
    
    # Create Flask app and get SQLite URI
    app = create_app()
    sqlite_uri = app.config['SQLALCHEMY_DATABASE_URI']
    
    print(f"\n📊 Source: SQLite database")
    
    # Create separate engines
    sqlite_engine = create_engine(sqlite_uri)
    postgres_engine = create_engine(pooler_url)
    
    # Test SQLite connection
    try:
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
        # Create backup
        print("\n💾 Creating backup...")
        import shutil
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"app.db.backup_{timestamp}"
        shutil.copy2("app.db", backup_name)
        print(f"✅ Backup created: {backup_name}")
        
        # Start migration
        print("\n🚀 Starting migration...")
        
        # Create sessions - IMPORTANT: Keep them separate!
        SqliteSession = sessionmaker(bind=sqlite_engine)
        sqlite_session = SqliteSession()
        
        # Temporarily update app config to PostgreSQL for table creation
        original_uri = app.config['SQLALCHEMY_DATABASE_URI']
        app.config['SQLALCHEMY_DATABASE_URI'] = pooler_url
        
        with app.app_context():
            # Create tables in PostgreSQL
            print("📋 Creating PostgreSQL tables...")
            db.create_all()
            print("✅ Tables created")
            
            # Get PostgreSQL session
            postgres_session = db.session
            
            # Migration order
            models = [
                (Client, "clients"),
                (Service, "services"), 
                (Quote, "quotes"),
                (QuoteItem, "quote items"),
                (Invoice, "invoices"),
                (InvoiceItem, "invoice items"),
                (Payment, "payments"),
                (EmailLog, "email logs"),
            ]
            
            total_migrated = 0
            
            for model_class, name in models:
                print(f"\n📦 Migrating {name}...")
                
                # Get SQLite data using SQLite session
                records = sqlite_session.query(model_class).all()
                count = len(records)
                
                if count == 0:
                    print(f"   No {name} to migrate")
                    continue
                
                print(f"   Found {count} {name}")
                
                # Migrate records to PostgreSQL
                migrated = 0
                for record in records:
                    try:
                        # Get record data
                        data = {}
                        for column in model_class.__table__.columns:
                            data[column.name] = getattr(record, column.name)
                        
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
                postgres_session.commit()
                print(f"   ✅ Migrated {migrated}/{count} {name}")
                total_migrated += migrated
            
            print(f"\n🎉 Migration complete! {total_migrated} records migrated")
            
            # Verify migration
            print("\n🔍 Verifying migration...")
            all_good = True
            
            for model_class, name in models:
                # Count in SQLite
                sqlite_count = sqlite_session.query(model_class).count()
                # Count in PostgreSQL
                postgres_count = postgres_session.query(model_class).count()
                
                if sqlite_count == postgres_count:
                    print(f"   ✅ {name}: {postgres_count} records")
                else:
                    print(f"   ❌ {name}: SQLite={sqlite_count}, PostgreSQL={postgres_count}")
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
        
        # Restore original URI and close sessions
        app.config['SQLALCHEMY_DATABASE_URI'] = original_uri
        sqlite_session.close()
        
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