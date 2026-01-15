#!/usr/bin/env python3
"""
Test when Supabase database becomes ready
"""

import socket
import time
from datetime import datetime

def test_hostname(hostname):
    """Test if hostname resolves"""
    try:
        socket.gethostbyname(hostname)
        return True
    except socket.gaierror:
        return False

def test_connection(database_url):
    """Test database connection"""
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return True
    except Exception:
        return False

def main():
    hostname = "db.urhejrvbaaxnkwcqvhur.supabase.co"
    database_url = "postgresql://postgres:2CYHK3RDQWLQTwtx@db.urhejrvbaaxnkwcqvhur.supabase.co:5432/postgres"
    
    print("🕐 Testing Supabase Database Readiness")
    print("=" * 40)
    print(f"Hostname: {hostname}")
    print(f"Testing every 30 seconds...")
    print("Press Ctrl+C to stop")
    print()
    
    attempt = 1
    while True:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] Attempt {attempt}:")
        
        # Test hostname resolution
        if test_hostname(hostname):
            print(f"  ✅ Hostname resolves")
            
            # Test database connection
            if test_connection(database_url):
                print(f"  ✅ Database connection successful!")
                print(f"\n🎉 Your Supabase database is ready!")
                print(f"You can now run the migration script.")
                break
            else:
                print(f"  ❌ Database connection failed (still initializing)")
        else:
            print(f"  ❌ Hostname not resolving yet")
        
        print(f"  Waiting 30 seconds...")
        print()
        
        try:
            time.sleep(30)
            attempt += 1
        except KeyboardInterrupt:
            print(f"\n\n⏹️  Monitoring stopped.")
            break

if __name__ == "__main__":
    main() 