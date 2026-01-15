#!/usr/bin/env python3
"""
Simple Migration Script - Using Flask App Context
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
    
    # Database URLs
    sqlite_url = "sqlite:///app.db"
    pooler_url = "postgresql://postgres.urhejrvbaaxnkwcqvhur:2CYHK3RDQWLQTwtx@aws-0-us-east-2.pooler.supabase.com:6543/postgres"
    
    print("🎯 Target: Supabase PostgreSQL (Pooler)")
    
    # Test connections
    print("\n🔍 Testing connections...")
    try:
        postgres_engine = create_engine(pooler_url)
        with postgres_engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ PostgreSQL: {version[:60]}...")
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False
    
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
        # Create backup
        print("\n💾 Creating backup...")
        import shutil
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"app.db.backup_{timestamp}"
        shutil.copy2("app.db", backup_name)
        print(f"✅ Backup created: {backup_name}")
        
        # Import Flask app and models
        from app import create_app, db
        from app.models.client import Client
        from app.models.service import Service
        from app.models.quote import Quote, QuoteItem
        from app.models.invoice import Invoice, InvoiceItem
        from app.models.payment import Payment
        from app.models.email_log import EmailLog
        
        # Create Flask app with PostgreSQL
        app = create_app()
        app.config['SQLALCHEMY_DATABASE_URI'] = pooler_url
        
        print("\n🚀 Starting migration...")
        
        # Create SQLite session
        SqliteSession = sessionmaker(bind=sqlite_engine)
        sqlite_session = SqliteSession()
        
        with app.app_context():
            # Create PostgreSQL tables
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
            
            for model_class, description in models:
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
                        db.session.add(new_record)
                        migrated += 1
                        
                        # Batch commit every 50 records
                        if migrated % 50 == 0:
                            db.session.commit()
                    
                    except Exception as e:
                        print(f"   ⚠️  Error with record {record.id}: {e}")
                        db.session.rollback()
                        continue
                
                # Final commit for this model
                try:
                    db.session.commit()
                    print(f"   ✅ Migrated {migrated}/{count} {description}")
                    total_migrated += migrated
                except Exception as e:
                    print(f"   ❌ Error committing {description}: {e}")
                    db.session.rollback()
            
            print(f"\n🎉 Migration complete! {total_migrated} records migrated")
            
            # Verify migration
            print("\n🔍 Verifying migration...")
            all_good = True
            
            for model_class, description in models:
                sqlite_count = sqlite_session.query(model_class).count()
                postgres_count = db.session.query(model_class).count()
                
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
        
        # Close SQLite session
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