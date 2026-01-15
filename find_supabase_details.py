#!/usr/bin/env python3
"""
Helper script to find Supabase connection details
"""

def main():
    print("🔍 How to Find Your Supabase Connection Details")
    print("=" * 50)
    print()
    print("1. Go to https://supabase.com/dashboard")
    print("2. Sign in to your account")
    print("3. Select your project from the list")
    print("4. In the left sidebar, click on 'Settings' (gear icon)")
    print("5. Click on 'Database' in the settings menu")
    print("6. Scroll down to find the 'Connection string' section")
    print("7. Look for the 'URI' connection string")
    print()
    print("The connection string should look like:")
    print("postgresql://postgres:[YOUR-PASSWORD]@db.abcdefghijklmnop.supabase.co:5432/postgres")
    print()
    print("Where:")
    print("- 'abcdefghijklmnop' is your unique project reference")
    print("- '[YOUR-PASSWORD]' is your database password")
    print()
    print("Alternative method:")
    print("1. In the same Database settings page")
    print("2. Look for 'Connection parameters' section")
    print("3. Find the 'Host' field - this is what you need")
    print()
    print("Common issues:")
    print("- Make sure you're using the correct project")
    print("- Verify your database password is correct")
    print("- Check that your project is not paused")
    print("- Ensure you have network connectivity")
    print()
    
    response = input("Do you want to try the setup again? (yes/no): ").lower().strip()
    if response in ['yes', 'y']:
        import subprocess
        subprocess.run(['python', 'setup_supabase.py'])

if __name__ == "__main__":
    main() 