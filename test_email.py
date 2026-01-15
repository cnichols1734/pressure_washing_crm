import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.getcwd())

from app import create_app
from flask_mail import Message

print("Starting email test...")

# Create the Flask app
app = create_app()
# Enter app context
with app.app_context():
    from app import mail
    
    # Try sending an email
    try:
        msg = Message(
            'Test email from AquaCRM',
            sender='aquaforcepressurewashingsvc@gmail.com',
            recipients=['aquaforcepressurewashingsvc@gmail.com']
        )
        msg.body = 'This is a test email from AquaCRM.'
        msg.html = '<p>This is a <b>test email</b> from AquaCRM.</p>'
        
        print('Trying to send email...')
        mail.send(msg)
        print('Email sent successfully!')
    except Exception as e:
        print(f'Error sending email: {e}')
        import traceback
        traceback.print_exc() 