#!/usr/bin/env python3
"""
Final Migration Script
This script uses the configuration from supabase_config.py to run the migration.
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def run_complete_migration():
    """Run the complete migration process"""
    print("🚀 AquaCRM SQLite to Supabase Migration")
    print("=" * 50)
    
    # Import configuration
    try:
        from supabase_config import get_database_url
        database_url = get_database_url()
        
        if not database_url:
            print("\n❌ Please configure your DATABASE_URL in supabase_config.py first.")
            return False
    except ImportError:
        print("❌ Could not import supabase_config.py")
        return False
    
    print(f"🎯 Target: {database_url.split('@')[1].split('/')[0]}")
    
    # Test connection first
    print("\n🔍 Testing Supabase connection...")
    try:
        test_engine = create_engine(database_url)
        with test_engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connection successful!")
            print(f"   PostgreSQL: {version[:60]}...")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nPlease check your DATABASE_URL in supabase_config.py")
        return False
    
    # Proceed with migration
    try:
        from app import create_app, db
        from app.models import Client, Quote, QuoteItem, Invoice, InvoiceItem, Payment, EmailLog, Service
        
        app = create_app()
        
        # Get current SQLite info
        sqlite_uri = app.config['SQLALCHEMY_DATABASE_URI']
        print(f"\n📊 Source: SQLite ({sqlite_uri})")
        
        # Create engines
        sqlite_engine = create_engine(sqlite_uri)
        postgres_engine = create_engine(database_url)
        
        # Check SQLite data
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
        
        # Set up sessions
        SqliteSession = sessionmaker(bind=sqlite_engine)
        sqlite_session = SqliteSession()
        
        # Temporarily switch to PostgreSQL
        original_uri = app.config['SQLALCHEMY_DATABASE_URI']
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        
        with app.app_context():
            # Create PostgreSQL tables
            print("\n📋 Creating PostgreSQL tables...")
            db.create_all()
            print("✅ Tables created successfully")
            
            # Define migration order
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
            
            # Migrate each model
            for model_class, name in models:
                print(f"\n📦 Migrating {name}...")
                
                # Get SQLite records
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
                        # Extract record data
                        data = {}
                        for column in model_class.__table__.columns:
                            data[column.name] = getattr(record, column.name)
                        
                        # Create new record in PostgreSQL
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
                print("\n🎊 Migration verification passed!")
                
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
                print("\n⚠️  Some data verification failed.")
                return False
        
        # Restore original URI
        app.config['SQLALCHEMY_DATABASE_URI'] = original_uri
        sqlite_session.close()
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = run_complete_migration()
        if success:
            print("\n✅ Migration completed successfully!")
        else:
            print("\n❌ Migration failed.")
    except KeyboardInterrupt:
        print("\n\n❌ Migration cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}") 