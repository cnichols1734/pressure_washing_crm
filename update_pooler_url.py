#!/usr/bin/env python3
"""
Update .env file with Supabase pooler URL
"""

import urllib.parse

# Your pooler connection details
password = "2CYHK3RDQWLQTwtx"  # Your current password
pooler_url = f"postgresql://postgres.urhejrvbaaxnkwcqvhur:{password}@aws-0-us-east-2.pooler.supabase.com:6543/postgres"

print("🔧 Updating DATABASE_URL with Pooler Connection")
print("=" * 50)
print(f"New URL: {pooler_url}")

# Read current .env file
with open('.env', 'r') as f:
    lines = f.readlines()

# Replace the DATABASE_URL line
new_lines = []
for line in lines:
    if line.startswith('DATABASE_URL='):
        new_lines.append(f'DATABASE_URL={pooler_url}\n')
    else:
        new_lines.append(line)

# Write back to .env file
with open('.env', 'w') as f:
    f.writelines(new_lines)

print("✅ .env file updated with pooler URL")
print("\nTesting connection...")

# Test the connection
try:
    from sqlalchemy import create_engine, text
    engine = create_engine(pooler_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.scalar()
        print(f"✅ Connection successful!")
        print(f"PostgreSQL: {version[:60]}...")
        print("\n🎉 Ready for migration!")
except Exception as e:
    print(f"❌ Connection failed: {e}") 