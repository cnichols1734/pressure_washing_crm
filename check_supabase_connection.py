#!/usr/bin/env python3
"""
Supabase Connection Checker
This script helps diagnose connection issues and find the correct connection details.
"""

import socket
import urllib.parse

def test_hostname(hostname):
    """Test if a hostname can be resolved"""
    try:
        socket.gethostbyname(hostname)
        return True
    except socket.gaierror:
        return False

def main():
    print("🔍 Supabase Connection Diagnostics")
    print("=" * 40)
    
    # Test the current hostname
    current_host = "db.urhejrvbaaxnkwcqvhur.supabase.co"
    print(f"\n1. Testing current hostname: {current_host}")
    
    if test_hostname(current_host):
        print("✅ Hostname resolves correctly")
    else:
        print("❌ Hostname does not resolve")
        print("\nPossible issues:")
        print("- Project reference ID might be incorrect")
        print("- Project might be paused in Supabase dashboard")
        print("- Hostname format might have changed")
    
    print("\n" + "=" * 40)
    print("🔧 How to find your correct connection details:")
    print()
    print("1. Go to https://supabase.com/dashboard")
    print("2. Sign in and select your project")
    print("3. Go to Settings > Database")
    print("4. Look for 'Connection string' section")
    print("5. Copy the complete 'URI' connection string")
    print()
    print("The URI should look like:")
    print("postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres")
    print()
    print("Common issues:")
    print("- Make sure your project is not paused")
    print("- Verify the project reference ID is correct")
    print("- Check that you're using the right project")
    print()
    print("Alternative connection methods:")
    print("- Try using the 'Connection pooling' URL if available")
    print("- Check if there's a different hostname format in your dashboard")

if __name__ == "__main__":
    main() 