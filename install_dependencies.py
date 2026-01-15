#!/usr/bin/env python3
"""
Install dependencies for Supabase migration
"""

import subprocess
import sys

def install_dependencies():
    """Install required dependencies for PostgreSQL support"""
    print("Installing PostgreSQL dependencies...")
    
    try:
        # Install psycopg2-binary
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary==2.9.7"])
        print("✓ psycopg2-binary installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False

if __name__ == "__main__":
    success = install_dependencies()
    if success:
        print("\n✅ Dependencies installed successfully!")
        print("You can now run the migration script: python migrate_to_supabase.py")
    else:
        print("\n❌ Failed to install dependencies.")
        print("Please install manually: pip install psycopg2-binary==2.9.7") 