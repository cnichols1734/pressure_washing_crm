#!/usr/bin/env python3
import os
from sqlalchemy import create_engine, text
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()
database_url = os.environ.get('DATABASE_URL')

def test_authentication():
    print("🔍 Authentication Test")
    print("=" * 30)
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            # Get user details
            result = conn.execute(text('SELECT id, username, email, password_hash FROM "user" WHERE username = :username'), 
                                {'username': 'ADMIN'})
            user = result.fetchone()
            
            if not user:
                print("❌ User 'ADMIN' not found!")
                return
            
            print(f"Found user: {user[1]} ({user[2]})")
            print(f"Password hash: {user[3][:50]}...")
            
            # Test password
            test_password = input("\nEnter password to test: ").strip()
            
            if check_password_hash(user[3], test_password):
                print("✅ Password is correct!")
            else:
                print("❌ Password is incorrect!")
                
                # Show what the hash should look like for this password
                correct_hash = generate_password_hash(test_password)
                print(f"\nFor password '{test_password}', the hash should be:")
                print(f"{correct_hash[:50]}...")
                print(f"\nBut the stored hash is:")
                print(f"{user[3][:50]}...")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_authentication() 