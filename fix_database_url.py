#!/usr/bin/env python3
"""
Fix DATABASE_URL formatting for special characters
"""

import urllib.parse

def fix_database_url():
    """Help format DATABASE_URL with proper URL encoding"""
    print("🔧 DATABASE_URL Formatter")
    print("=" * 30)
    print()
    print("This tool will help you create a properly formatted DATABASE_URL")
    print("for your Supabase connection with special characters in the password.")
    print()
    
    # Get components
    host = "db.urhejrvbaaxnkwcqvhur.supabase.co"
    port = "5432"
    database = "postgres"
    username = "postgres"
    
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Database: {database}")
    print(f"Username: {username}")
    print()
    
    # Get password
    password = input("Enter your Supabase database password: ").strip()
    
    if not password:
        print("❌ Password is required!")
        return None
    
    # URL encode the password to handle special characters
    encoded_password = urllib.parse.quote(password, safe='')
    
    # Create the DATABASE_URL
    database_url = f"postgresql://{username}:{encoded_password}@{host}:{port}/{database}"
    
    print()
    print("✅ Formatted DATABASE_URL:")
    print(f"DATABASE_URL={database_url}")
    print()
    print("Copy this line and add it to your .env file:")
    print(f"DATABASE_URL={database_url}")
    
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

def main():
    """Main function"""
    database_url = fix_database_url()
    
    if database_url:
        test_response = input("\nTest this connection? (yes/no): ").lower().strip()
        if test_response in ['yes', 'y']:
            if test_connection(database_url):
                print("\n🎉 Success! Your DATABASE_URL is correctly formatted.")
                print("\nNext steps:")
                print("1. Copy the DATABASE_URL line above to your .env file")
                print("2. Run: python simple_migrate.py")
            else:
                print("\n❌ Connection test failed. Please check your password.")

if __name__ == "__main__":
    main() 