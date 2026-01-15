#!/usr/bin/env python3
"""
Automated Supabase Migration Script
This script will handle the complete migration process automatically.
"""

import os
import sys
import subprocess
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def get_database_url_from_user():
    """Get DATABASE_URL from user input"""
    print("🚀 Automated Supabase Migration")
    print("=" * 40)
    print()
    print("I need your Supabase DATABASE_URL to proceed.")
    print("Please go to your Supabase dashboard:")
    print("1. Settings > Database")
    print("2. Copy the 'URI' connection string")
    print()
    print("It should look like:")
    print("postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres")
    print()
    
    while True:
        database_url = input("Enter your DATABASE_URL: ").strip()
        
        if not database_url:
            print("❌ DATABASE_URL cannot be empty. Please try again.")
            continue
            
        if not database_url.startswith('postgresql://'):
            print("❌ Invalid format. URL must start with 'postgresql://'. Please try again.")
            continue
            
        return database_url

def update_env_file(database_url):
    """Update the .env file with the new DATABASE_URL"""
    print("📝 Updating .env file...")
    
    # Read existing .env content
    env_content = []
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            env_content = f.readlines()
    
    # Remove any existing DATABASE_URL
    env_content = [line for line in env_content if not line.startswith('DATABASE_URL=')]
    
    # Add the new DATABASE_URL
    env_content.append(f'DATABASE_URL={database_url}\n')
    
    # Write back to .env file
    with open('.env', 'w') as f:
        f.writelines(env_content)
    
    print("✅ .env file updated with DATABASE_URL")

def test_connection(database_url):
    """Test the database connection"""
    print("🔍 Testing Supabase connection...")
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connection successful!")
            print(f"   PostgreSQL: {version[:60]}...")
            return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def run_migration():
    """Run the actual migration using the existing script"""
    print("\n🚀 Starting migration process...")
    
    try:
        # Import and run migration
        from app import create_app, db
        from app.models import Client, Quote, QuoteItem, Invoice, InvoiceItem, Payment, EmailLog, Service
        
        app = create_app()
        
        # Get database URLs
        sqlite_uri = app.config['SQLALCHEMY_DATABASE_URI']
        postgres_uri = os.environ.get('DATABASE_URL')
        
        print(f"📊 Source: SQLite ({sqlite_uri})")
        print(f"🎯 Target: PostgreSQL (Supabase)")
        
        # Create engines
        sqlite_engine = create_engine(sqlite_uri)
        postgres_engine = create_engine(postgres_uri)
        
        # Test SQLite connection
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
        
        # Create sessions
        SqliteSession = sessionmaker(bind=sqlite_engine)
        sqlite_session = SqliteSession()
        
        # Temporarily update app config to use PostgreSQL
        original_uri = app.config['SQLALCHEMY_DATABASE_URI']
        app.config['SQLALCHEMY_DATABASE_URI'] = postgres_uri
        
        with app.app_context():
            # Create all tables in PostgreSQL
            print("\n📋 Creating PostgreSQL tables...")
            db.create_all()
            print("✅ Tables created successfully")
            
            # Migration order (respecting foreign key dependencies)
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
                
                # Get data from SQLite
                records = sqlite_session.query(model_class).all()
                count = len(records)
                
                if count == 0:
                    print(f"   No {name} to migrate")
                    continue
                
                print(f"   Found {count} {name}")
                
                # Migrate each record
                migrated = 0
                for record in records:
                    try:
                        # Get all column values
                        data = {}
                        for column in model_class.__table__.columns:
                            data[column.name] = getattr(record, column.name)
                        
                        # Create new record
                        new_record = model_class(**data)
                        db.session.add(new_record)
                        migrated += 1
                        
                        # Commit in batches
                        if migrated % 50 == 0:
                            db.session.commit()
                    
                    except Exception as e:
                        print(f"   ⚠️  Error with record {record.id}: {e}")
                        db.session.rollback()
                        continue
                
                # Final commit for this model
                try:
                    db.session.commit()
                    print(f"   ✅ Successfully migrated {migrated}/{count} {name}")
                    total_migrated += migrated
                except Exception as e:
                    print(f"   ❌ Error committing {name}: {e}")
                    db.session.rollback()
            
            print(f"\n🎉 Migration completed! Total records migrated: {total_migrated}")
            
            # Verify migration
            print("\n🔍 Verifying migration...")
            verification_passed = True
            
            for model_class, name in models:
                sqlite_count = sqlite_session.query(model_class).count()
                postgres_count = db.session.query(model_class).count()
                
                if sqlite_count == postgres_count:
                    print(f"   ✅ {name}: {postgres_count} records")
                else:
                    print(f"   ❌ {name}: SQLite={sqlite_count}, PostgreSQL={postgres_count}")
                    verification_passed = False
            
            if verification_passed:
                print("\n🎊 Migration verification passed! All data migrated successfully.")
                return True
            else:
                print("\n⚠️  Migration verification failed. Some data may not have migrated correctly.")
                return False
        
        # Restore original database URI
        app.config['SQLALCHEMY_DATABASE_URI'] = original_uri
        sqlite_session.close()
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to run the complete migration"""
    try:
        # Step 1: Get DATABASE_URL from user
        database_url = get_database_url_from_user()
        
        # Step 2: Test the connection
        if not test_connection(database_url):
            print("\n❌ Cannot proceed with migration due to connection issues.")
            print("Please check your DATABASE_URL and try again.")
            return
        
        # Step 3: Update .env file
        update_env_file(database_url)
        
        # Step 4: Set environment variable for this session
        os.environ['DATABASE_URL'] = database_url
        
        # Step 5: Run the migration
        success = run_migration()
        
        if success:
            print("\n🎉 MIGRATION COMPLETED SUCCESSFULLY!")
            print("=" * 50)
            print("✅ All data has been migrated to Supabase PostgreSQL")
            print("✅ Your .env file has been updated")
            print("✅ Your app is now configured to use Supabase")
            print()
            print("🚀 Next steps:")
            print("1. Restart your Flask application")
            print("2. Test all functionality to ensure everything works")
            print("3. Once satisfied, you can remove the SQLite database files")
            print()
            print("Your app will now use Supabase PostgreSQL for all database operations!")
        else:
            print("\n❌ Migration failed. Please check the errors above.")
            print("Your original SQLite database remains unchanged.")
    
    except KeyboardInterrupt:
        print("\n\n❌ Migration cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 