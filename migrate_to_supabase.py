#!/usr/bin/env python3
"""
SQLite to Supabase PostgreSQL Migration Script
This script migrates all data from your local SQLite database to Supabase PostgreSQL.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from flask import Flask
from app import create_app, db
from app.models import Client, Quote, QuoteItem, Invoice, InvoiceItem, Payment, EmailLog, Service
import getpass
from datetime import datetime

def get_supabase_url():
    """Get the Supabase database URL with password"""
    # Get the full database URL from environment or prompt user
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        print("Using DATABASE_URL from environment")
        return database_url
    
    # If no DATABASE_URL, ask for Supabase details
    print("Please provide your Supabase database connection details:")
    print("You can find these in your Supabase dashboard under Settings > Database")
    
    host = input("Database Host (e.g., db.xxxxxxxxxxxxx.supabase.co): ").strip()
    if not host:
        print("Error: Host is required")
        sys.exit(1)
    
    password = os.environ.get('SUPABASE_PASSWORD')
    if not password:
        password = getpass.getpass("Database Password: ")
    
    database_url = f"postgresql://postgres:{password}@{host}:5432/postgres"
    return database_url

def test_connections(sqlite_engine, postgres_engine):
    """Test both database connections"""
    print("Testing database connections...")
    
    try:
        # Test SQLite connection
        with sqlite_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='table'"))
            table_count = result.scalar()
            print(f"✓ SQLite connection successful - Found {table_count} tables")
    except Exception as e:
        print(f"✗ SQLite connection failed: {e}")
        return False
    
    try:
        # Test PostgreSQL connection
        with postgres_engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✓ PostgreSQL connection successful - {version[:50]}...")
    except Exception as e:
        print(f"✗ PostgreSQL connection failed: {e}")
        print("Please check your password and network connection.")
        return False
    
    return True

def backup_sqlite_data():
    """Create a backup of the SQLite database"""
    import shutil
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"app.db.backup_{timestamp}"
    
    try:
        shutil.copy2("app.db", backup_name)
        print(f"✓ SQLite backup created: {backup_name}")
        return backup_name
    except Exception as e:
        print(f"✗ Failed to create backup: {e}")
        return None

def migrate_data(app, postgres_url):
    """Migrate all data from SQLite to PostgreSQL"""
    
    # Create engines
    sqlite_engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    postgres_engine = create_engine(postgres_url)
    
    if not test_connections(sqlite_engine, postgres_engine):
        return False
    
    # Create backup
    backup_file = backup_sqlite_data()
    if not backup_file:
        print("Warning: Could not create backup, continuing anyway...")
    
    print("\nStarting migration process...")
    
    try:
        # Create sessions
        SqliteSession = sessionmaker(bind=sqlite_engine)
        PostgresSession = sessionmaker(bind=postgres_engine)
        
        sqlite_session = SqliteSession()
        
        # Temporarily update the app config to use PostgreSQL
        original_uri = app.config['SQLALCHEMY_DATABASE_URI']
        app.config['SQLALCHEMY_DATABASE_URI'] = postgres_url
        
        with app.app_context():
            # Create all tables in PostgreSQL
            print("Creating tables in PostgreSQL...")
            db.create_all()
            print("✓ Tables created successfully")
            
            # Get PostgreSQL session
            postgres_session = db.session
            
            # Migration order (respecting foreign key dependencies)
            migration_steps = [
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
            
            for model_class, description in migration_steps:
                print(f"\nMigrating {description}...")
                
                # Get data from SQLite
                sqlite_records = sqlite_session.query(model_class).all()
                count = len(sqlite_records)
                
                if count == 0:
                    print(f"  No {description} to migrate")
                    continue
                
                print(f"  Found {count} {description} to migrate")
                
                # Migrate each record
                migrated_count = 0
                for record in sqlite_records:
                    try:
                        # Create a new instance for PostgreSQL
                        # Get all column values
                        record_dict = {}
                        for column in model_class.__table__.columns:
                            record_dict[column.name] = getattr(record, column.name)
                        
                        # Create new instance
                        new_record = model_class(**record_dict)
                        postgres_session.add(new_record)
                        migrated_count += 1
                        
                        # Commit in batches of 100
                        if migrated_count % 100 == 0:
                            postgres_session.commit()
                            print(f"  Migrated {migrated_count}/{count} {description}")
                    
                    except Exception as e:
                        print(f"  Error migrating {description} record {record.id}: {e}")
                        postgres_session.rollback()
                        continue
                
                # Final commit for this model
                try:
                    postgres_session.commit()
                    print(f"✓ Successfully migrated {migrated_count}/{count} {description}")
                    total_migrated += migrated_count
                except Exception as e:
                    print(f"✗ Error committing {description}: {e}")
                    postgres_session.rollback()
            
            print(f"\n✓ Migration completed! Total records migrated: {total_migrated}")
            
            # Verify migration
            print("\nVerifying migration...")
            verification_passed = True
            
            for model_class, description in migration_steps:
                sqlite_count = sqlite_session.query(model_class).count()
                postgres_count = postgres_session.query(model_class).count()
                
                if sqlite_count == postgres_count:
                    print(f"✓ {description}: {postgres_count} records")
                else:
                    print(f"✗ {description}: SQLite has {sqlite_count}, PostgreSQL has {postgres_count}")
                    verification_passed = False
            
            if verification_passed:
                print("\n🎉 Migration verification passed! All data migrated successfully.")
            else:
                print("\n⚠️  Migration verification failed. Some data may not have migrated correctly.")
        
        # Restore original database URI
        app.config['SQLALCHEMY_DATABASE_URI'] = original_uri
        
        sqlite_session.close()
        return verification_passed
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        # Restore original database URI
        app.config['SQLALCHEMY_DATABASE_URI'] = original_uri
        return False

def update_env_file(postgres_url):
    """Update or create .env file with new database URL"""
    env_content = []
    env_file = '.env'
    
    # Read existing .env file if it exists
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            env_content = f.readlines()
    
    # Remove existing DATABASE_URL if present
    env_content = [line for line in env_content if not line.startswith('DATABASE_URL=')]
    
    # Add new DATABASE_URL
    env_content.append(f'DATABASE_URL={postgres_url}\n')
    
    # Write back to .env file
    with open(env_file, 'w') as f:
        f.writelines(env_content)
    
    print(f"✓ Updated {env_file} with new DATABASE_URL")

def main():
    """Main migration function"""
    print("🚀 SQLite to Supabase PostgreSQL Migration Tool")
    print("=" * 50)
    
    # Get Supabase URL
    postgres_url = get_supabase_url()
    
    # Create Flask app
    app = create_app()
    
    print(f"\nCurrent SQLite database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"Target PostgreSQL database: {postgres_url.replace(postgres_url.split(':')[2].split('@')[0], '***')}")
    
    # Confirm migration
    response = input("\nDo you want to proceed with the migration? (yes/no): ").lower().strip()
    if response not in ['yes', 'y']:
        print("Migration cancelled.")
        return
    
    # Perform migration
    success = migrate_data(app, postgres_url)
    
    if success:
        # Update .env file
        update_response = input("\nDo you want to update your .env file to use PostgreSQL? (yes/no): ").lower().strip()
        if update_response in ['yes', 'y']:
            update_env_file(postgres_url)
            print("\n✅ Migration completed successfully!")
            print("Your application is now configured to use Supabase PostgreSQL.")
            print("\nNext steps:")
            print("1. Restart your Flask application")
            print("2. Test your application to ensure everything works correctly")
            print("3. Consider removing the SQLite database file after confirming everything works")
        else:
            print("\n✅ Migration completed successfully!")
            print("Remember to update your DATABASE_URL environment variable to use PostgreSQL.")
    else:
        print("\n❌ Migration failed. Your SQLite database remains unchanged.")
        print("Please check the error messages above and try again.")

if __name__ == "__main__":
    main() 