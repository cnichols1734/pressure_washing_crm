#!/usr/bin/env python3

from app import create_app, db
from app.models import User
import os

def check_sqlite_database():
    app = create_app()
    with app.app_context():
        print('🔍 Checking SQLite Database')
        print('Database URI:', app.config['SQLALCHEMY_DATABASE_URI'])
        
        # Check if database file exists
        db_path = os.path.join(os.path.dirname(__file__), 'app.db')
        if os.path.exists(db_path):
            print(f'✅ Database file exists: {db_path}')
            print(f'   Size: {os.path.getsize(db_path)} bytes')
        else:
            print(f'❌ Database file not found: {db_path}')
            return False
        
        # Check if we can connect and query
        try:
            users = User.query.all()
            print(f'✅ Found {len(users)} users in SQLite database')
            for user in users:
                print(f'   - {user.username} ({user.email})')
            return True
        except Exception as e:
            print(f'❌ Error accessing database: {e}')
            print('   Database may need to be initialized')
            return False

if __name__ == '__main__':
    check_sqlite_database() 