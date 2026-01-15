#!/usr/bin/env python3
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
database_url = os.environ.get('DATABASE_URL')

try:
    engine = create_engine(database_url)
    with engine.connect() as conn:
        # Check if clients table exists
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'clients'"))
        table_exists = result.fetchone()
        
        if table_exists:
            print('✓ clients table exists')
            # Get table structure
            result = conn.execute(text("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'clients' ORDER BY ordinal_position"))
            columns = result.fetchall()
            print('Table structure:')
            for col in columns:
                print(f'  {col[0]}: {col[1]} (nullable: {col[2]})')
        else:
            print('✗ clients table does not exist')
            
        # List all tables
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = result.fetchall()
        print(f'\nAll tables: {[t[0] for t in tables]}')
        
except Exception as e:
    print(f'Error: {e}') 