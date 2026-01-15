#!/usr/bin/env python3
"""
Supabase Setup Script
This script helps you configure your Supabase database connection.
"""

import os
import getpass

def setup_supabase():
    """Interactive setup for Supabase connection"""
    print("🔧 Supabase Database Setup")
    print("=" * 40)
    print()
    print("To find your Supabase connection details:")
    print("1. Go to your Supabase dashboard (https://supabase.com/dashboard)")
    print("2. Select your project")
    print("3. Go to Settings > Database")
    print("4. Look for 'Connection string' section")
    print()
    
    # Get connection details
    print("Please provide your Supabase connection details:")
    print()
    
    host = input("Database Host (e.g., db.abcdefghijklmnop.supabase.co): ").strip()
    if not host:
        print("❌ Host is required!")
        return None
    
    password = getpass.getpass("Database Password: ")
    if not password:
        print("❌ Password is required!")
        return None
    
    # Construct the database URL
    database_url = f"postgresql://postgres:{password}@{host}:5432/postgres"
    
    print()
    print("✅ Configuration complete!")
    print()
    print("Your DATABASE_URL is:")
    print(f"postgresql://postgres:***@{host}:5432/postgres")
    
    return database_url

def test_connection(database_url):
    """Test the database connection"""
    print("\n🧪 Testing connection...")
    
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connection successful!")
            print(f"PostgreSQL version: {version[:80]}...")
            return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def save_to_env_file(database_url):
    """Save the database URL to .env file"""
    env_content = []
    env_file = '.env'
    
    # Read existing .env file if it exists
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            env_content = f.readlines()
    
    # Remove existing DATABASE_URL if present
    env_content = [line for line in env_content if not line.startswith('DATABASE_URL=')]
    
    # Add new DATABASE_URL
    env_content.append(f'DATABASE_URL={database_url}\n')
    
    # Add other common variables if they don't exist
    existing_vars = [line.split('=')[0] for line in env_content if '=' in line]
    
    if 'SECRET_KEY' not in existing_vars:
        env_content.append('SECRET_KEY=dev-key-please-change-in-production\n')
    
    # Write back to .env file
    with open(env_file, 'w') as f:
        f.writelines(env_content)
    
    print(f"✅ Saved configuration to {env_file}")

def main():
    """Main setup function"""
    database_url = setup_supabase()
    
    if not database_url:
        print("❌ Setup failed. Please try again.")
        return
    
    # Test the connection
    if test_connection(database_url):
        # Save to environment file
        save_response = input("\nSave this configuration to .env file? (yes/no): ").lower().strip()
        if save_response in ['yes', 'y']:
            save_to_env_file(database_url)
            print("\n🎉 Setup complete!")
            print("\nNext steps:")
            print("1. Run: python test_migration_setup.py")
            print("2. If tests pass, run: python migrate_to_supabase.py")
        else:
            print(f"\nTo use this configuration, set the environment variable:")
            print(f"export DATABASE_URL='{database_url}'")
    else:
        print("\n❌ Connection test failed. Please check your details and try again.")

if __name__ == "__main__":
    main() 