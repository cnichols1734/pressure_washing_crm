#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import re

def test_client_creation_flow():
    print("🧪 Testing Full Client Creation Flow")
    print("=" * 45)
    
    base_url = "http://localhost:5003"
    session = requests.Session()
    
    try:
        # Step 1: Get login page
        print("1. Getting login page...")
        login_response = session.get(f"{base_url}/login")
        if login_response.status_code != 200:
            print(f"❌ Failed to get login page: {login_response.status_code}")
            return
        print("✅ Login page loaded")
        
        # Step 2: Login
        print("2. Logging in...")
        login_data = {
            'username': 'ADMIN',
            'password': 'Cassiechris177!',
            'remember': 'true'
        }
        login_submit = session.post(f"{base_url}/login", data=login_data, allow_redirects=True)
        if "Invalid username or password" in login_submit.text:
            print("❌ Login failed - invalid credentials")
            return
        print("✅ Login successful")
        
        # Step 3: Get client creation page
        print("3. Getting client creation page...")
        create_response = session.get(f"{base_url}/clients/create")
        if create_response.status_code != 200:
            print(f"❌ Failed to get client creation page: {create_response.status_code}")
            return
        print("✅ Client creation page loaded")
        
        # Step 4: Parse CSRF token
        soup = BeautifulSoup(create_response.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})
        if csrf_token:
            csrf_value = csrf_token.get('value')
            print(f"✅ CSRF token found: {csrf_value[:20]}...")
        else:
            print("⚠️  No CSRF token found")
            csrf_value = ""
        
        # Step 5: Submit client creation form
        print("4. Creating test client...")
        client_data = {
            'csrf_token': csrf_value,
            'name': 'Test Client via Web',
            'email': 'webtest@example.com',
            'phone': '555-123-4567',
            'address1': '123 Test Street',
            'city': 'Test City',
            'state': 'TS',
            'zip_code': '12345'
        }
        
        create_submit = session.post(f"{base_url}/clients/create", data=client_data, allow_redirects=True)
        
        if "Client created successfully" in create_submit.text:
            print("✅ Client created successfully via web interface!")
        elif "An error occurred" in create_submit.text or "error" in create_submit.text.lower():
            print("❌ Error occurred during client creation")
            print("Response content preview:")
            print(create_submit.text[:500])
        else:
            print("⚠️  Unexpected response")
            print(f"Status code: {create_submit.status_code}")
            print("Response content preview:")
            print(create_submit.text[:500])
        
        # Step 6: Check clients list
        print("5. Checking clients list...")
        clients_response = session.get(f"{base_url}/clients/")
        if "Test Client via Web" in clients_response.text:
            print("✅ New client appears in clients list")
        else:
            print("⚠️  New client not found in clients list")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_client_creation_flow() 