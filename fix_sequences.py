#!/usr/bin/env python3
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
database_url = os.environ.get('DATABASE_URL')

def fix_sequences():
    print("🔧 Fixing Auto-Increment Sequences")
    print("=" * 40)
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            # Get all tables with id columns
            tables_to_fix = [
                'clients', 'quotes', 'quote_items', 'invoices', 
                'invoice_items', 'payments', 'email_logs', 'services', 'user'
            ]
            
            for table in tables_to_fix:
                try:
                    # Check if table exists
                    result = conn.execute(text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')"))
                    table_exists = result.scalar()
                    
                    if not table_exists:
                        print(f"⚠️  Table '{table}' does not exist, skipping...")
                        continue
                    
                    # Get the current max ID
                    result = conn.execute(text(f"SELECT COALESCE(MAX(id), 0) FROM {table}"))
                    max_id = result.scalar()
                    
                    # Reset the sequence
                    sequence_name = f"{table}_id_seq"
                    new_value = max_id + 1
                    
                    with conn.begin():
                        conn.execute(text(f"SELECT setval('{sequence_name}', {new_value})"))
                    
                    print(f"✅ Fixed sequence for '{table}' - next ID will be {new_value}")
                    
                except Exception as e:
                    print(f"❌ Error fixing sequence for '{table}': {e}")
            
            print("\n🎉 Sequence fix complete!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_sequences() 