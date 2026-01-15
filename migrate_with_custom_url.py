#!/usr/bin/env python3
"""
Migration Script with Custom DATABASE_URL Input
This script allows you to input your DATABASE_URL directly and run the migration.
"""

import os
import sys
import getpass
import urllib.parse
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app import create_app, db
from app.models import Client, Quote, QuoteItem, Invoice, InvoiceItem, Payment, EmailLog, Service

def get_database_url():
    """Get DATABASE_URL from user input"""
    print("🔧 Enter Your Supabase DATABASE_URL")
    print("=" * 40)
    print()
    print("Please go to your Supabase dashboard:")
    print("1. Settings > Database")
    print("2. Copy the complete 'URI' connection string")
    print("3. Paste it below")
    print()
    print("Example format:")
    print("postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres")
    print()
    
    database_url = input("Enter your complete DATABASE_URL: ").strip()
    
    if not database_url:
        print("❌ DATABASE_URL is required!")
        return None
    
    if not database_url.startswith('postgresql://'):
        print("❌ Invalid format. Must start with 'postgresql://'")
        return None
    
    return database_url

def test_connection(database_url):
    """Test the database connection"""
    print("\n🔍 Testing connection...")
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connection successful!")
            print(f"PostgreSQL: {version[:60]}...")
            return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def run_migration(database_url):
    """Run the complete migration"""
    try:
        # Create Flask app
        app = create_app()
        
        print(f"\n📊 Source: SQLite database")
        print(f"🎯 Target: Supabase PostgreSQL")
        
        # Create engines
        sqlite_engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
        postgres_engine = create_engine(database_url)
        
        # Test SQLite
        with sqlite_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='table'"))
            table_count = result.scalar()
            print(f"✅ SQLite: {table_count} tables found")
        
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
        sqlite_session = SqliteSession()
        
        # Temporarily update app config
        original_uri = app.config['SQLALCHEMY_DATABASE_URI']
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        
        with app.app_context():
            # Create tables
            print("📋 Creating PostgreSQL tables...")
            db.create_all()
            print("✅ Tables created")
            
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
                
                # Get SQLite data
                records = sqlite_session.query(model_class).all()
                count = len(records)
                
                if count == 0:
                    print(f"   No {name} to migrate")
                    continue
                
                print(f"   Found {count} {name}")
                
                # Migrate records
                migrated = 0
                for record in records:
                    try:
                        # Get record data
                        data = {}
                        for column in model_class.__table__.columns:
                            data[column.name] = getattr(record, column.name)
                        
                        # Create new record
                        new_record = model_class(**data)
                        db.session.add(new_record)
                        migrated += 1
                        
                        # Batch commit
                        if migrated % 50 == 0:
                            db.session.commit()
                    
                    except Exception as e:
                        print(f"   ⚠️  Error with record {record.id}: {e}")
                        db.session.rollback()
                        continue
                
                # Final commit
                db.session.commit()
                print(f"   ✅ Migrated {migrated}/{count} {name}")
                total_migrated += migrated
            
            print(f"\n🎉 Migration complete! {total_migrated} records migrated")
            
            # Verify
            print("\n🔍 Verifying migration...")
            all_good = True
            
            for model_class, name in models:
                sqlite_count = sqlite_session.query(model_class).count()
                postgres_count = db.session.query(model_class).count()
                
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
                env_content.append(f'DATABASE_URL={database_url}\n')
                
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
        
        # Restore original URI
        app.config['SQLALCHEMY_DATABASE_URI'] = original_uri
        sqlite_session.close()
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("🚀 AquaCRM SQLite to Supabase Migration")
    print("=" * 50)
    
    # Get DATABASE_URL
    database_url = get_database_url()
    if not database_url:
        return False
    
    # Test connection
    if not test_connection(database_url):
        print("\n❌ Connection test failed. Please check your DATABASE_URL.")
        return False
    
    # Confirm migration
    response = input("\nProceed with migration? (yes/no): ").lower().strip()
    if response not in ['yes', 'y']:
        print("Migration cancelled.")
        return False
    
    # Run migration
    return run_migration(database_url)

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