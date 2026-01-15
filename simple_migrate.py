#!/usr/bin/env python3
"""
Simple Migration Script - Uses DATABASE_URL from .env file
"""

import os
from dotenv import load_dotenv
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app import create_app, db
from app.models import Client, Quote, QuoteItem, Invoice, InvoiceItem, Payment, EmailLog, Service

def main():
    """Main migration function"""
    print("🚀 Supabase Migration Tool")
    print("=" * 30)
    
    # Load environment variables
    load_dotenv()
    
    # Check for DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables.")
        print("\nPlease add this line to your .env file:")
        print("DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.urhejrvbaaxnkwcqvhur.supabase.co:5432/postgres")
        print("\nReplace YOUR_PASSWORD with your actual Supabase password.")
        return False
    
    if not database_url.startswith('postgresql://'):
        print("❌ Invalid DATABASE_URL format. Must start with 'postgresql://'")
        return False
    
    print(f"✅ Found DATABASE_URL in environment")
    
    # Create Flask app
    app = create_app()
    
    print(f"\n📊 Current: SQLite database")
    print(f"🎯 Target: Supabase PostgreSQL")
    
    # Confirm migration
    response = input("\nProceed with migration? (yes/no): ").lower().strip()
    if response not in ['yes', 'y']:
        print("Migration cancelled.")
        return False
    
    try:
        # Test connections
        print("\n🔍 Testing connections...")
        
        # Test SQLite
        sqlite_engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
        with sqlite_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='table'"))
            table_count = result.scalar()
            print(f"✅ SQLite: {table_count} tables found")
        
        # Test PostgreSQL
        postgres_engine = create_engine(database_url)
        with postgres_engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ PostgreSQL: Connected successfully")
        
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
                print("\n🚀 Your app is now configured to use Supabase PostgreSQL!")
                print("\nNext steps:")
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
        print("Please check your DATABASE_URL and network connection.")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Migration completed successfully!")
    else:
        print("\n❌ Migration failed. Check errors above.") 