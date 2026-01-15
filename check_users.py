#!/usr/bin/env python3
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
database_url = os.environ.get('DATABASE_URL')
print(f'Connecting to: {database_url[:50]}...')

try:
    engine = create_engine(database_url)
    with engine.connect() as conn:
        result = conn.execute(text('SELECT id, username, email, password_hash FROM "user" ORDER BY created_at DESC LIMIT 5'))
        users = result.fetchall()
        print(f'Found {len(users)} users:')
        for user in users:
            print(f'  ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Password Hash: {user[3][:20]}...')
        
        # Test password verification
        print("\nTesting password verification...")
        from werkzeug.security import check_password_hash
        
        for user in users:
            print(f"\nUser: {user[1]}")
            print(f"Hash: {user[3]}")
            # Try some common passwords
            test_passwords = ['password', '123456', 'admin', 'test', user[1]]
            for pwd in test_passwords:
                if check_password_hash(user[3], pwd):
                    print(f"  ✓ Password '{pwd}' matches!")
                    break
            else:
                print("  ✗ None of the test passwords match")
                
except Exception as e:
    print(f'Error: {e}') 