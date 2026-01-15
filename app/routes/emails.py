from flask import Blueprint, jsonify, request
from datetime import datetime
from app import db, mail
from flask_mail import Message
from app.models import EmailLog, Client, Quote, Invoice

bp = Blueprint('emails', __name__, url_prefix='/api/emails')

@bp.route('/', methods=['GET'])
def get_emails():
    """Get all email logs."""
    emails = EmailLog.query.all()
    return jsonify([{
        'id': email.id,
        'client_id': email.client_id,
        'quote_id': email.quote_id,
        'invoice_id': email.invoice_id,
        'email_type': email.email_type,
        'subject': email.subject,
        'recipient': email.recipient,
        'sent_at': email.sent_at
    } for email in emails])

@bp.route('/<int:id>', methods=['GET'])
def get_email(id):
    """Get a specific email log."""
    email = EmailLog.query.get_or_404(id)
    return jsonify({
        'id': email.id,
        'client_id': email.client_id,
        'quote_id': email.quote_id,
        'invoice_id': email.invoice_id,
        'email_type': email.email_type,
        'subject': email.subject,
        'body': email.body,
        'recipient': email.recipient,
        'sent_at': email.sent_at
    })

@bp.route('/send-quote/<int:quote_id>', methods=['POST'])
def send_quote_email(quote_id):
    """Send a quote email."""
    quote = Quote.query.get_or_404(quote_id)
    client = Client.query.get(quote.client_id)
    
    if not client.email:
        return jsonify({'error': 'Client has no email address'}), 400
    
    # Create email content
    subject = f'Your Quote #{quote.quote_number} from Aquaforce Pressure Washing'
    data = request.get_json() or {}
    custom_message = data.get('message', '')
    
    # Professional HTML template
    body = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Quote #{quote.quote_number}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            
            body {{
                font-family: 'Inter', Arial, sans-serif;
                line-height: 1.6;
                color: #1a1a1a;
                margin: 0;
                padding: 0;
                background-color: #f8fafc;
            }}
            .container {{
                max-width: 650px;
                margin: 20px auto;
                padding: 0;
                background-color: #ffffff;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
                overflow: hidden;
            }}
            .header {{
                text-align: center;
                padding: 30px 20px;
                background: white;
                color: #333;
                position: relative;
                margin-bottom: 10px;
            }}
            .header::after {{
                content: '';
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                height: 1px;
                background: #e2e8f0;
            }}
            .logo {{
                margin-bottom: 10px;
            }}
            .logo img {{
                max-width: 350px;
                height: auto;
            }}
            .quote-number {{
                font-size: 22px;
                font-weight: 600;
                padding: 6px 12px;
                display: inline-block;
                color: #2d3748;
            }}
            .subtitle {{
                font-size: 16px;
                opacity: 0.9;
                margin-bottom: 16px;
            }}
            .content {{
                padding: 40px;
            }}
            .greeting {{
                margin-bottom: 32px;
            }}
            .greeting p {{
                margin: 0 0 16px 0;
                font-size: 16px;
                color: #4b5563;
            }}
            .quote-summary {{
                background-color: #f0f9ff;
                padding: 24px;
                border-radius: 8px;
                margin-bottom: 32px;
                border: 1px solid #e0f2fe;
            }}
            .quote-summary strong {{
                display: block;
                font-size: 18px;
                color: #0f172a;
                margin-bottom: 16px;
            }}
            .quote-summary p {{
                margin: 8px 0;
                color: #475569;
            }}
            .services-info {{
                background-color: #f0fdf4;
                padding: 24px;
                border-radius: 8px;
                margin-bottom: 32px;
                border: 1px solid #dcfce7;
            }}
            .services-info strong {{
                display: block;
                font-size: 18px;
                color: #0f172a;
                margin-bottom: 16px;
            }}
            .services-info p {{
                margin: 8px 0;
                color: #475569;
            }}
            table {{
                width: 100%;
                border-collapse: separate;
                border-spacing: 0;
                margin-bottom: 32px;
            }}
            th {{
                background-color: #f8fafc;
                color: #0f172a;
                text-align: left;
                padding: 16px;
                font-weight: 600;
                border-bottom: 2px solid #e2e8f0;
            }}
            td {{
                padding: 16px;
                border-bottom: 1px solid #e2e8f0;
                color: #475569;
            }}
            .total-row {{
                font-weight: 600;
                background-color: #f8fafc;
            }}
            .total-row td {{
                color: #0f172a;
                font-size: 16px;
            }}
            .notes {{
                background-color: #f8fafc;
                padding: 24px;
                border-radius: 8px;
                margin-bottom: 32px;
                border: 1px solid #e2e8f0;
            }}
            .notes strong {{
                display: block;
                font-size: 16px;
                color: #0f172a;
                margin-bottom: 12px;
            }}
            .notes p {{
                margin: 0;
                color: #475569;
            }}
            .footer {{
                text-align: center;
                padding: 32px 40px;
                background-color: #f8fafc;
                border-top: 1px solid #e2e8f0;
            }}
            .footer p {{
                margin: 8px 0;
                color: #64748b;
                font-size: 14px;
            }}
            .contact-info {{
                margin-top: 16px;
                padding-top: 16px;
                border-top: 1px solid #e2e8f0;
            }}
            .contact-info p {{
                margin: 4px 0;
                color: #64748b;
            }}
            @media (max-width: 600px) {{
                .container {{
                    margin: 0;
                    border-radius: 0;
                }}
                .content {{
                    padding: 24px;
                }}
                .header {{
                    padding: 32px 16px;
                }}
                .logo {{
                    font-size: 28px;
                }}
                table {{
                    display: block;
                    overflow-x: auto;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">
                    <img src="cid:company_logo" alt="Aquaforce Pressure Washing">
                </div>
                <div class="quote-number">Quote #{quote.quote_number}</div>
            </div>
            
            <div class="content">
                <div class="greeting">
                    <p>Dear {client.name},</p>
                    <p>{custom_message if custom_message else 'Thank you for your interest in our services. Please find your detailed quote below.'}</p>
                </div>
                
                <div class="quote-summary">
                    <strong>Quote Summary</strong>
                    <p>Date Created: {quote.date_created.strftime('%B %d, %Y') if hasattr(quote.date_created, 'strftime') else quote.date_created}</p>
                    <p>Valid Until: {quote.valid_until.strftime('%B %d, %Y') if hasattr(quote.valid_until, 'strftime') else quote.valid_until}</p>
                    <p>Total Amount: <strong>${float(quote.total):.2f}</strong></p>
                </div>
                
                <div class="services-info">
                    <strong>Our Services Include</strong>
                    <p>• Professional Pressure Washing<br>• Surface Cleaning<br>• Deck & Patio Cleaning<br>• Roof Cleaning<br>• Gutter Cleaning</p>
                </div>
                
                <table>
                    <tr>
                        <th>Service Description</th>
                        <th>Quantity</th>
                        <th>Unit Price</th>
                        <th>Total</th>
                    </tr>
    """
    
    # Add items to email
    for item in quote.items:
        body += f"""
                    <tr>
                        <td>{item.description}</td>
                        <td>{float(item.quantity)}</td>
                        <td>${float(item.unit_price):.2f}</td>
                        <td>${float(item.line_total):.2f}</td>
                    </tr>
        """
    
    body += f"""
                    <tr class="total-row">
                        <td colspan="3" align="right">Total:</td>
                        <td>${float(quote.total):.2f}</td>
                    </tr>
                </table>
    """
                
    if quote.notes:
        body += f"""
                <div class="notes">
                    <strong>Notes:</strong>
                    <p>{quote.notes}</p>
                </div>
        """
                
    body += """
                <p>If you have any questions about this quote, please don't hesitate to contact us.</p>
                <p>We look forward to working with you!</p>
                <p>Best regards,<br>Aquaforce Pressure Washing Team</p>
            </div>
            
            <div class="footer">
                <div class="contact-info">
                    <p><strong>Aquaforce Pressure Washing</strong></p>
                    <p>Phone: (713) 725-4459</p>
                    <p>Email: aquaforcepressurewashingsvc@gmail.com</p>
                    <p>Website: www.aquaforcepressurewashing.com</p>
                </div>
                <p>© 2024 Aquaforce Pressure Washing. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Save email log before sending
    email_log = EmailLog(
        client_id=client.id,
        quote_id=quote.id,
        email_type='quote',
        subject=subject,
        body=body,
        recipient=client.email,
        sent_at=datetime.utcnow()
    )
    
    db.session.add(email_log)
    
    # Update quote status
    quote.status = 'sent'
    
    # Create and send the email
    msg = Message(subject, recipients=[client.email])
    msg.html = body
    
    # Attach the logo
    with open('app/static/img/AFLOGO.png', 'rb') as fp:
        msg.attach('AFLOGO.png', 'image/png', fp.read(), 'inline', headers=[('Content-ID', '<company_logo>')])
    
    mail.send(msg)
    
    db.session.commit()
    
    return jsonify({
        'message': f'Quote {quote.quote_number} email sent successfully to {client.email}',
        'email_log_id': email_log.id
    })

@bp.route('/send-invoice/<int:invoice_id>', methods=['POST'])
def send_invoice_email(invoice_id):
    """Send an invoice email."""
    # Debug logging
    with open('app/routes/debug_log.txt', 'a') as f:
        f.write(f"[{datetime.utcnow()}] Starting send_invoice_email for invoice_id={invoice_id}\n")
    
    invoice = Invoice.query.get_or_404(invoice_id)
    client = Client.query.get(invoice.client_id)
    
    # Debug logging
    with open('app/routes/debug_log.txt', 'a') as f:
        f.write(f"[{datetime.utcnow()}] Client: {client.name}, Email: {client.email}\n")
    
    if not client.email:
        with open('app/routes/debug_log.txt', 'a') as f:
            f.write(f"[{datetime.utcnow()}] Error: Client has no email address\n")
        return jsonify({'error': 'Client has no email address'}), 400
    
    # Create email content
    subject = f'Invoice #{invoice.invoice_number} from Aquaforce Pressure Washing'
    data = request.get_json() or {}
    custom_message = data.get('message', '')
    
    # Debug logging
    with open('app/routes/debug_log.txt', 'a') as f:
        f.write(f"[{datetime.utcnow()}] Subject: {subject}, Custom message: {custom_message}\n")
    
    # Professional HTML template
    body = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Invoice #{invoice.invoice_number}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333333;
                margin: 0;
                padding: 0;
                background-color: #f9f9f9;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #ffffff;
                border-radius: 5px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                text-align: center;
                padding: 20px 0;
                background-color: #0c4da2;
                color: white;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                margin-bottom: 20px;
            }}
            .logo {{
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            .invoice-number {{
                font-size: 18px;
                margin-bottom: 10px;
            }}
            .content {{
                padding: 20px;
            }}
            .greeting {{
                margin-bottom: 20px;
            }}
            .invoice-details {{
                margin-bottom: 20px;
            }}
            .invoice-summary {{
                background-color: #f5f8ff;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
            .payment-info {{
                background-color: #e9f7ff;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
                border-left: 4px solid #0c4da2;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            th {{
                background-color: #0c4da2;
                color: white;
                text-align: left;
                padding: 10px;
            }}
            td {{
                padding: 10px;
                border-bottom: 1px solid #eeeeee;
            }}
            .total-row {{
                font-weight: bold;
                background-color: #f5f8ff;
            }}
            .notes {{
                background-color: #f9f9f9;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                font-size: 12px;
                color: #666666;
                background-color: #f5f8ff;
                border-bottom-left-radius: 5px;
                border-bottom-right-radius: 5px;
            }}
            .cta-button {{
                display: inline-block;
                background-color: #0c4da2;
                color: white;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">AQUAFORCE</div>
                <div>PRESSURE WASHING</div>
                <div class="invoice-number">Invoice #{invoice.invoice_number}</div>
            </div>
            
            <div class="content">
                <div class="greeting">
                    <p>Dear {client.name},</p>
                    <p>{custom_message if custom_message else 'Thank you for choosing Aquaforce Pressure Washing. Please find your invoice details below.'}</p>
                </div>
                
                <div class="invoice-summary">
                    <strong>Invoice Summary</strong>
                    <p>Date Issued: {invoice.date_issued.strftime('%B %d, %Y') if hasattr(invoice.date_issued, 'strftime') else invoice.date_issued}</p>
                    <p>Due Date: {invoice.due_date.strftime('%B %d, %Y') if hasattr(invoice.due_date, 'strftime') else invoice.due_date}</p>
                    <p>Total Amount: <strong>${float(invoice.total):.2f}</strong></p>
                </div>
                
                <div class="payment-info">
                    <strong>Payment Information</strong>
                    <p>Please remit payment by the due date. For your convenience, we accept:</p>
                    <p>• Credit/Debit Cards<br>• Cash<br>• Venmo/Cash App/Zelle</p>
                </div>
                
                <table>
                    <tr>
                        <th>Service Description</th>
                        <th>Quantity</th>
                        <th>Unit Price</th>
                        <th>Total</th>
                    </tr>
    """
    
    # Add items to email
    for item in invoice.items:
        body += f"""
                    <tr>
                        <td>{item.description}</td>
                        <td>{int(item.quantity)}</td>
                        <td>${float(item.unit_price):.2f}</td>
                        <td>${float(item.line_total):.2f}</td>
                    </tr>
        """
    
    body += f"""
                    <tr class="total-row">
                        <td colspan="3" align="right">Total:</td>
                        <td>${float(invoice.total):.2f}</td>
                    </tr>
                </table>
    """
                
    if invoice.notes:
        body += f"""
                <div class="notes">
                    <strong>Notes:</strong>
                    <p>{invoice.notes}</p>
                </div>
        """
                
    body += """
                <p>If you have any questions about this invoice, please don't hesitate to contact us.</p>
                <p>Thank you for your business!</p>
                <p>Best regards,<br>Aquaforce Pressure Washing Team</p>
            </div>
            
            <div class="footer">
                <div class="contact-info">
                    <p><strong>Aquaforce Pressure Washing</strong></p>
                    <p>Phone: (713) 725-4459</p>
                    <p>Email: aquaforcepressurewashingsvc@gmail.com</p>
                    <p>Website: www.aquaforcepressurewashing.com</p>
                </div>
                <p>© 2023 Aquaforce Pressure Washing. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Save email log before sending
    email_log = EmailLog(
        client_id=client.id,
        invoice_id=invoice.id,
        email_type='invoice',
        subject=subject,
        body=body,
        recipient=client.email,
        sent_at=datetime.utcnow()
    )
    
    db.session.add(email_log)
    
    # Update invoice status
    invoice.status = 'sent'
    
    # Create and send the email
    try:
        with open('app/routes/debug_log.txt', 'a') as f:
            f.write(f"[{datetime.utcnow()}] Attempting to send email via Flask-Mail\n")
            f.write(f"[{datetime.utcnow()}] Mail config: SERVER={mail.state.server}, PORT={mail.state.port}, USERNAME={mail.state.username}\n")
        
        msg = Message(subject, recipients=[client.email])
        msg.html = body
        mail.send(msg)
        with open('app/routes/debug_log.txt', 'a') as f:
            f.write(f"[{datetime.utcnow()}] Email sent successfully to {client.email}\n")
    except Exception as e:
        import traceback
        with open('app/routes/debug_log.txt', 'a') as f:
            f.write(f"[{datetime.utcnow()}] Error sending email: {str(e)}\n")
            f.write(f"[{datetime.utcnow()}] Traceback: {traceback.format_exc()}\n")
        # Still commit the EmailLog record even if sending fails
        db.session.commit()
        return jsonify({'error': f'Failed to send email: {str(e)}'}), 500
    
    db.session.commit()
    
    with open('app/routes/debug_log.txt', 'a') as f:
        f.write(f"[{datetime.utcnow()}] Email logged and committed to database\n")
    
    return jsonify({
        'message': f'Invoice {invoice.invoice_number} email sent successfully to {client.email}',
        'email_log_id': email_log.id
    })

@bp.route('/test-email', methods=['GET'])
def test_email():
    """Test email sending without login requirement."""
    import os
    
    # Create a debug log file in the root directory
    log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'email_debug.log')
    
    with open(log_path, 'a') as f:
        f.write(f"[{datetime.utcnow()}] Starting test_email function\n")
    
    try:
        with open(log_path, 'a') as f:
            f.write(f"[{datetime.utcnow()}] Attempting to send test email via Flask-Mail\n")
            try:
                server = getattr(mail.state, 'server', 'unknown')
                port = getattr(mail.state, 'port', 'unknown')
                username = getattr(mail.state, 'username', 'unknown')
                f.write(f"[{datetime.utcnow()}] Mail config: SERVER={server}, PORT={port}, USERNAME={username}\n")
            except Exception as config_e:
                f.write(f"[{datetime.utcnow()}] Error getting mail config: {str(config_e)}\n")
        
        recipient = 'aquaforcepressurewashingsvc@gmail.com'  # Hardcoded for testing
        
        # Professional HTML test email
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Test Email</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333333;
                    margin: 0;
                    padding: 0;
                    background-color: #f9f9f9;
                }
                .container {
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #ffffff;
                    border-radius: 5px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                }
                .header {
                    text-align: center;
                    padding: 20px 0;
                    background-color: #0c4da2;
                    color: white;
                    border-top-left-radius: 5px;
                    border-top-right-radius: 5px;
                    margin-bottom: 20px;
                }
                .logo {
                    font-size: 24px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }
                .content {
                    padding: 20px;
                }
                .footer {
                    text-align: center;
                    padding: 20px;
                    font-size: 12px;
                    color: #666666;
                    background-color: #f5f8ff;
                    border-bottom-left-radius: 5px;
                    border-bottom-right-radius: 5px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">AQUAFORCE</div>
                    <div>PRESSURE WASHING</div>
                </div>
                
                <div class="content">
                    <h2>Test Email</h2>
                    <p>This is a test email from Aquaforce Pressure Washing's CRM system.</p>
                    <p>If you're receiving this email, it means our email system is working correctly.</p>
                    <p>Thank you!</p>
                    <p>Best regards,<br>Aquaforce Pressure Washing Team</p>
                </div>
                
                <div class="footer">
                    <p>Aquaforce Pressure Washing | Phone: (555) 123-4567 | Email: info@aquaforcepressurewashing.com</p>
                    <p>© 2023 Aquaforce Pressure Washing. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg = Message(
            subject="Aquaforce Pressure Washing - Test Email", 
            recipients=[recipient],
            body="This is a test email from Aquaforce Pressure Washing.",
            html=html_content
        )
        
        mail.send(msg)
        
        with open(log_path, 'a') as f:
            f.write(f"[{datetime.utcnow()}] Test email sent successfully to {recipient}\n")
            
        return jsonify({"message": "Test email sent successfully!"})
        
    except Exception as e:
        import traceback
        with open(log_path, 'a') as f:
            f.write(f"[{datetime.utcnow()}] Error sending test email: {str(e)}\n")
            f.write(f"[{datetime.utcnow()}] Traceback: {traceback.format_exc()}\n")
            
        return jsonify({"error": f"Failed to send test email: {str(e)}"}), 500 