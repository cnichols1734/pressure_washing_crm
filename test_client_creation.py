#!/usr/bin/env python3
from app import create_app, db
from app.models import Client

app = create_app()
with app.app_context():
    try:
        # Test creating a client directly
        client = Client(
            name='Test Client',
            email='test@example.com',
            phone='123-456-7890'
        )
        db.session.add(client)
        db.session.commit()
        print('✓ Client created successfully')
        print(f'Client ID: {client.id}')
        
        # Clean up
        db.session.delete(client)
        db.session.commit()
        print('✓ Test client deleted')
        
    except Exception as e:
        print(f'✗ Error creating client: {e}')
        import traceback
        traceback.print_exc() 