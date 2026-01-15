#!/usr/bin/env python3
"""
Supabase Configuration
Set your DATABASE_URL here and run the migration.
"""

# REPLACE THIS WITH YOUR ACTUAL SUPABASE DATABASE_URL
# You can find this in your Supabase dashboard under Settings > Database
# Copy the "URI" connection string

DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_ID.supabase.co:5432/postgres"

# Example:
# DATABASE_URL = "postgresql://postgres:mypassword123@db.abcdefghijklmnop.supabase.co:5432/postgres"

def get_database_url():
    """Get the configured DATABASE_URL"""
    if DATABASE_URL == "postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_ID.supabase.co:5432/postgres":
        print("❌ Please update the DATABASE_URL in supabase_config.py with your actual Supabase connection string.")
        print()
        print("To find your DATABASE_URL:")
        print("1. Go to https://supabase.com/dashboard")
        print("2. Select your project")
        print("3. Go to Settings > Database")
        print("4. Copy the 'URI' connection string")
        print("5. Replace the DATABASE_URL in supabase_config.py")
        print("6. Run this script again")
        return None
    
    return DATABASE_URL

if __name__ == "__main__":
    url = get_database_url()
    if url:
        print(f"✅ DATABASE_URL configured: {url.split('@')[1].split('/')[0]}")
    else:
        print("❌ DATABASE_URL not configured yet.") 