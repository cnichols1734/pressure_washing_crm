#!/usr/bin/env python3
"""
Fix the DATABASE_URL in .env file by URL-encoding the password
"""

import urllib.parse

# Your password with special characters
password = "RA!9&WXze9dZ+#s"

# URL encode the password
encoded_password = urllib.parse.quote(password, safe='')

# Create the correct DATABASE_URL
database_url = f"postgresql://postgres:{encoded_password}@db.urhejrvbaaxnkwcqvhur.supabase.co:5432/postgres"

print(f"Original password: {password}")
print(f"Encoded password: {encoded_password}")
print(f"Correct DATABASE_URL: {database_url}")

# Read current .env file
with open('.env', 'r') as f:
    lines = f.readlines()

# Replace the DATABASE_URL line
new_lines = []
for line in lines:
    if line.startswith('DATABASE_URL='):
        new_lines.append(f'DATABASE_URL={database_url}\n')
    else:
        new_lines.append(line)

# Write back to .env file
with open('.env', 'w') as f:
    f.writelines(new_lines)

print("\n✅ .env file updated with properly encoded DATABASE_URL") 