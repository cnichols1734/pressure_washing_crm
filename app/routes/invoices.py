from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash
from datetime import datetime, timedelta
from app import db
from app.models import Invoice, InvoiceItem, Client, Quote, QuoteItem
from flask_login import login_required
from app.forms import InvoiceForm
from app.routes.emails import send_invoice_email

# Create two blueprints - one for API and one for web interface
api_bp = Blueprint('api_invoices', __name__, url_prefix='/api/invoices')
bp = Blueprint('invoices', __name__, url_prefix='/invoices')

# Web Interface Routes
@bp.route('/')
@login_required
def index():
    """Display list of invoices."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Invoice.query
    if search:
        query = query.filter(Invoice.invoice_number.ilike(f'%{search}%'))
    
    pagination = query.order_by(Invoice.date_issued.desc()).paginate(
        page=page, per_page=10, error_out=False)
    invoices = pagination.items
    
    return render_template('invoices/index.html', invoices=invoices, pagination=pagination)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new invoice."""
    from decimal import Decimal
    
    client_id = request.args.get('client_id', type=int)
    quote_id = request.args.get('quote_id', type=int)
    
    # On POST, also check form data for quote_id
    if request.method == 'POST' and not quote_id:
        quote_id = request.form.get('quote_id', type=int)
    
    form = InvoiceForm()
    clients = Client.query.order_by(Client.name).all()
    form.client_id.choices = [(c.id, c.name) for c in clients]
    
    # Initialize variables for template
    quote = None
    prefilled_items = []
    
    # Handle quote pre-filling
    if quote_id:
        quote = Quote.query.get_or_404(quote_id)
        
        # Check if quote is accepted
        if quote.status != 'accepted':
            flash('Only accepted quotes can be converted to invoices.', 'warning')
            return redirect(url_for('quotes.view', id=quote_id))
        
        # Check if already has invoice
        if quote.invoice:
            flash('This quote already has an invoice.', 'warning')
            return redirect(url_for('invoices.view', id=quote.invoice.id))
        
        # Pre-populate form fields
        form.client_id.data = quote.client_id
        
        # Generate invoice number
        year = datetime.now().year
        last_invoice = Invoice.query.filter(Invoice.invoice_number.like(f'INV-{year}-%')).order_by(Invoice.id.desc()).first()
        if last_invoice:
            last_number = int(last_invoice.invoice_number.split('-')[-1])
            invoice_number = f'INV-{year}-{last_number + 1:03d}'
        else:
            invoice_number = f'INV-{year}-001'
        
        form.invoice_number.data = invoice_number
        form.date_issued.data = datetime.now().date()
        form.due_date.data = datetime.now().date() + timedelta(days=30)
        form.status.data = 'draft'
        form.notes.data = quote.notes
        
        # Prepare line items from quote
        prefilled_items = [
            {
                'description': item.description,
                'quantity': float(item.quantity),
                'unit_price': float(item.unit_price),
                'line_total': float(item.line_total)
            }
            for item in quote.items
        ]
    elif client_id:
        form.client_id.data = client_id
    
    if request.method == 'POST':
        # Generate invoice number if not from quote
        if not quote_id:
            year = datetime.now().year
            last_invoice = Invoice.query.filter(Invoice.invoice_number.like(f'INV-{year}-%')).order_by(Invoice.id.desc()).first()
            if last_invoice:
                last_number = int(last_invoice.invoice_number.split('-')[-1])
                invoice_number = f'INV-{year}-{last_number + 1:03d}'
            else:
                invoice_number = f'INV-{year}-001'
        else:
            invoice_number = request.form.get('invoice_number')
        
        # Create invoice with basic fields
        invoice = Invoice(
            client_id=request.form.get('client_id'),
            quote_id=quote_id if quote_id else None,
            invoice_number=invoice_number,
            date_issued=datetime.strptime(request.form.get('date_issued'), '%Y-%m-%d').date(),
            due_date=datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date(),
            status=request.form.get('status', 'draft'),
            notes=request.form.get('notes', '')
        )
        db.session.add(invoice)
        db.session.flush()  # Get invoice ID for line items
        
        # Process line items from form
        i = 0
        while f'items[{i}][description]' in request.form:
            description = request.form.get(f'items[{i}][description]')
            quantity_str = request.form.get(f'items[{i}][quantity]')
            unit_price_str = request.form.get(f'items[{i}][unit_price]')
            
            # Convert to Decimal to match database field types
            try:
                quantity = Decimal(quantity_str) if quantity_str else Decimal('0')
            except (ValueError, TypeError):
                quantity = Decimal('0')
            
            try:
                unit_price = Decimal(unit_price_str) if unit_price_str else Decimal('0')
            except (ValueError, TypeError):
                unit_price = Decimal('0')
            
            if description:  # Only create if description is provided
                item = InvoiceItem(
                    invoice_id=invoice.id,
                    description=description,
                    quantity=quantity,
                    unit_price=unit_price
                )
                item.calculate_line_total()
                db.session.add(item)
            
            i += 1
        
        # Calculate invoice total
        db.session.flush()  # Ensure all items are saved
        invoice.calculate_total()
        
        db.session.commit()
        
        flash('Invoice created successfully.', 'success')
        
        # If created from a quote, redirect back to the quote to show the invoice was created
        if quote_id:
            return redirect(url_for('quotes.view', id=quote_id))
        else:
            return redirect(url_for('invoices.view', id=invoice.id))
    
    return render_template('invoices/form.html', form=form, clients=clients, invoice=None, quote=quote, prefilled_items=prefilled_items)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit an invoice."""
    invoice = Invoice.query.get_or_404(id)
    form = InvoiceForm(obj=invoice)
    # Populate client choices
    form.client_id.choices = [(c.id, c.name) for c in Client.query.order_by(Client.name).all()]
    
    if form.validate_on_submit():
        invoice.client_id = form.client_id.data
        invoice.invoice_number = form.invoice_number.data
        invoice.date_issued = form.date_issued.data
        invoice.due_date = form.due_date.data
        invoice.description = form.description.data
        invoice.subtotal = form.subtotal.data
        invoice.tax_rate = form.tax_rate.data
        invoice.tax_amount = form.tax_amount.data
        invoice.total = form.total.data
        invoice.status = form.status.data
        invoice.notes = form.notes.data
        
        db.session.commit()
        
        flash('Invoice updated successfully.', 'success')
        return redirect(url_for('invoices.view', id=invoice.id))
    
    return render_template('invoices/form.html', form=form, invoice=invoice)

@bp.route('/<int:id>')
@login_required
def view(id):
    """View a specific invoice."""
    invoice = Invoice.query.get_or_404(id)
    return render_template('invoices/view.html', invoice=invoice)

@bp.route('/<int:id>/send')
@login_required
def send(id):
    """Send invoice to client."""
    invoice = Invoice.query.get_or_404(id)
    
    # Directly use the email function's internals
    try:
        # Import needed functions
        from app.routes.emails import send_invoice_email
        from flask import jsonify
        
        # Get client and prepare basics
        client = Client.query.get(invoice.client_id)
        if not client.email:
            flash('Client has no email address', 'error')
            return redirect(url_for('invoices.view', id=invoice.id))
            
        # Create email content
        from datetime import datetime
        from app.models import EmailLog
        from app import mail, db
        from flask_mail import Message
        
        subject = f'Invoice #{invoice.invoice_number} from Aquaforce Pressure Washing'
        custom_message = ""  # No custom message for direct sends
        
        # Professional HTML template
        body = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Invoice #{invoice.invoice_number}</title>
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
                .invoice-number {{
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
                .invoice-summary {{
                    background-color: #f0f9ff;
                    padding: 24px;
                    border-radius: 8px;
                    margin-bottom: 32px;
                    border: 1px solid #e0f2fe;
                }}
                .invoice-summary strong {{
                    display: block;
                    font-size: 18px;
                    color: #0f172a;
                    margin-bottom: 16px;
                }}
                .invoice-summary p {{
                    margin: 8px 0;
                    color: #475569;
                }}
                .payment-info {{
                    background-color: #f0fdf4;
                    padding: 24px;
                    border-radius: 8px;
                    margin-bottom: 32px;
                    border: 1px solid #dcfce7;
                }}
                .payment-info strong {{
                    display: block;
                    font-size: 18px;
                    color: #0f172a;
                    margin-bottom: 16px;
                }}
                .payment-info p {{
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
                    <p>© 2024 Aquaforce Pressure Washing. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Save email log
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
        msg = Message(subject, recipients=[client.email])
        msg.html = body
        
        # Attach the logo
        with open('app/static/img/AFLOGO.png', 'rb') as fp:
            msg.attach('AFLOGO.png', 'image/png', fp.read(), 'inline', headers=[('Content-ID', '<company_logo>')])
        
        mail.send(msg)
        
        db.session.commit()
        
        flash('Invoice sent successfully!', 'success')
    except Exception as e:
        flash(f'Error sending invoice: {str(e)}', 'error')
    
    return redirect(url_for('invoices.view', id=invoice.id))

# API Routes
@api_bp.route('/', methods=['GET'])
def get_invoices():
    """Get all invoices."""
    invoices = Invoice.query.all()
    return jsonify([{
        'id': invoice.id,
        'client_id': invoice.client_id,
        'invoice_number': invoice.invoice_number,
        'date_issued': invoice.date_issued.isoformat(),
        'due_date': invoice.due_date.isoformat(),
        'description': invoice.description,
        'subtotal': float(invoice.subtotal),
        'tax_rate': float(invoice.tax_rate),
        'tax_amount': float(invoice.tax_amount),
        'total': float(invoice.total),
        'status': invoice.status
    } for invoice in invoices])

@api_bp.route('/<int:id>', methods=['GET'])
def get_invoice(id):
    """Get a specific invoice."""
    invoice = Invoice.query.get_or_404(id)
    return jsonify({
        'id': invoice.id,
        'client_id': invoice.client_id,
        'invoice_number': invoice.invoice_number,
        'date_issued': invoice.date_issued.isoformat(),
        'due_date': invoice.due_date.isoformat(),
        'description': invoice.description,
        'subtotal': float(invoice.subtotal),
        'tax_rate': float(invoice.tax_rate),
        'tax_amount': float(invoice.tax_amount),
        'total': float(invoice.total),
        'status': invoice.status
    })

@api_bp.route('/', methods=['POST'])
def create_invoice():
    """Create a new invoice."""
    data = request.get_json() or {}
    
    required_fields = ['client_id', 'invoice_number', 'date_issued', 'due_date', 'subtotal', 'tax_rate', 'tax_amount', 'total']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    invoice = Invoice(
        client_id=data['client_id'],
        invoice_number=data['invoice_number'],
        date_issued=datetime.fromisoformat(data['date_issued']),
        due_date=datetime.fromisoformat(data['due_date']),
        total=data['total'],
        status=data.get('status', 'draft'),
        notes=data.get('notes', '')
    )
    
    db.session.add(invoice)
    db.session.commit()
    
    return jsonify({
        'id': invoice.id,
        'client_id': invoice.client_id,
        'invoice_number': invoice.invoice_number,
        'date_issued': invoice.date_issued.isoformat(),
        'due_date': invoice.due_date.isoformat(),
        'description': invoice.description,
        'subtotal': float(invoice.subtotal),
        'tax_rate': float(invoice.tax_rate),
        'tax_amount': float(invoice.tax_amount),
        'total': float(invoice.total),
        'status': invoice.status
    }), 201

@api_bp.route('/<int:id>', methods=['PUT'])
def update_invoice(id):
    """Update an invoice."""
    invoice = Invoice.query.get_or_404(id)
    data = request.get_json() or {}
    
    # Update invoice fields
    if 'client_id' in data:
        invoice.client_id = data['client_id']
    if 'invoice_number' in data:
        invoice.invoice_number = data['invoice_number']
    if 'date_issued' in data:
        invoice.date_issued = datetime.fromisoformat(data['date_issued'])
    if 'due_date' in data:
        invoice.due_date = datetime.fromisoformat(data['due_date'])
    if 'description' in data:
        invoice.description = data['description']
    if 'subtotal' in data:
        invoice.subtotal = data['subtotal']
    if 'tax_rate' in data:
        invoice.tax_rate = data['tax_rate']
    if 'tax_amount' in data:
        invoice.tax_amount = data['tax_amount']
    if 'total' in data:
        invoice.total = data['total']
    if 'status' in data:
        invoice.status = data['status']
    if 'notes' in data:
        invoice.notes = data['notes']
    
    # Update items if provided
    if 'items' in data and isinstance(data['items'], list):
        # First, get existing items
        existing_items = {item.id: item for item in invoice.items}
        
        for item_data in data['items']:
            if 'id' in item_data and item_data['id'] in existing_items:
                # Update existing item
                item = existing_items[item_data['id']]
                for field in ['description', 'quantity', 'unit_price']:
                    if field in item_data:
                        setattr(item, field, item_data[field])
                item.calculate_line_total()
            else:
                # Create new item
                item = InvoiceItem(
                    invoice_id=invoice.id,
                    description=item_data.get('description', ''),
                    quantity=item_data.get('quantity', 1),
                    unit_price=item_data.get('unit_price', 0)
                )
                item.calculate_line_total()
                db.session.add(item)
        
        # Delete items not in the update
        if 'delete_items' in data and isinstance(data['delete_items'], list):
            for item_id in data['delete_items']:
                if item_id in existing_items:
                    db.session.delete(existing_items[item_id])
    
    db.session.commit()
    
    return jsonify({
        'id': invoice.id,
        'client_id': invoice.client_id,
        'invoice_number': invoice.invoice_number,
        'date_issued': invoice.date_issued.isoformat(),
        'due_date': invoice.due_date.isoformat(),
        'description': invoice.description,
        'subtotal': float(invoice.subtotal),
        'tax_rate': float(invoice.tax_rate),
        'tax_amount': float(invoice.tax_amount),
        'total': float(invoice.total),
        'status': invoice.status
    })

@api_bp.route('/<int:id>', methods=['DELETE'])
def delete_invoice(id):
    """Delete an invoice."""
    invoice = Invoice.query.get_or_404(id)
    db.session.delete(invoice)
    db.session.commit()
    
    return jsonify({'message': 'Invoice deleted successfully'})

@api_bp.route('/from-quote/<int:quote_id>', methods=['POST'])
def create_from_quote(quote_id):
    """Create a new invoice from a quote."""
    quote = Quote.query.get_or_404(quote_id)

    # Check if quote is already invoiced
    if quote.invoice:
        return jsonify({'error': 'Quote already has an invoice'}), 400

    # Generate invoice number (format: INV-YYYY-NNN)
    year = datetime.now().year
    last_invoice = Invoice.query.filter(Invoice.invoice_number.like(f'INV-{year}-%')).order_by(Invoice.id.desc()).first()
    if last_invoice:
        last_number = int(last_invoice.invoice_number.split('-')[-1])
        invoice_number = f'INV-{year}-{last_number + 1:03d}'
    else:
        invoice_number = f'INV-{year}-001'

    # Set dates
    date_issued = datetime.now().date()
    due_date = date_issued + timedelta(days=30)

    # Create invoice
    invoice = Invoice(
        client_id=quote.client_id,
        quote_id=quote.id,
        invoice_number=invoice_number,
        date_issued=date_issued,
        due_date=due_date,
        notes=quote.notes,
        total=0,
        status='draft'
    )
    db.session.add(invoice)
    db.session.flush()  # Get invoice ID

    # Copy quote items to invoice items
    total = 0
    for q_item in quote.items:
        item = InvoiceItem(
            invoice_id=invoice.id,
            description=q_item.description,
            quantity=q_item.quantity,
            unit_price=q_item.unit_price,
            line_total=q_item.line_total
        )
        total += float(q_item.line_total)
        db.session.add(item)

    invoice.total = total
    db.session.commit()

    return jsonify({'id': invoice.id})

@api_bp.route('/<int:id>/send', methods=['POST'])
def send_invoice_api(id):
    """Send invoice to client via email (API endpoint)."""
    invoice = Invoice.query.get_or_404(id)
    data = request.get_json() or {}
    
    try:
        # Get client and prepare basics
        client = Client.query.get(invoice.client_id)
        if not client.email:
            return jsonify({'error': 'Client has no email address'}), 400
            
        # Create email content
        subject = f'Invoice #{invoice.invoice_number} from Aquaforce Pressure Washing'
        custom_message = data.get('message', '')
        
        # Professional HTML template matching quote style
        body = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Invoice #{invoice.invoice_number}</title>
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
                .invoice-number {{
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
                .invoice-summary {{
                    background-color: #f0f9ff;
                    padding: 24px;
                    border-radius: 8px;
                    margin-bottom: 32px;
                    border: 1px solid #e0f2fe;
                }}
                .invoice-summary strong {{
                    display: block;
                    font-size: 18px;
                    color: #0f172a;
                    margin-bottom: 16px;
                }}
                .invoice-summary p {{
                    margin: 8px 0;
                    color: #475569;
                }}
                .payment-info {{
                    background-color: #f0fdf4;
                    padding: 24px;
                    border-radius: 8px;
                    margin-bottom: 32px;
                    border: 1px solid #dcfce7;
                }}
                .payment-info strong {{
                    display: block;
                    font-size: 18px;
                    color: #0f172a;
                    margin-bottom: 16px;
                }}
                .payment-info p {{
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
                    <p>© 2024 Aquaforce Pressure Washing. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Save email log
        from app.models import EmailLog
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
        from flask_mail import Message
        from app import mail
        msg = Message(subject, recipients=[client.email])
        msg.html = body
        
        # Attach the logo
        with open('app/static/img/AFLOGO.png', 'rb') as fp:
            msg.attach('AFLOGO.png', 'image/png', fp.read(), 'inline', headers=[('Content-ID', '<company_logo>')])
        
        mail.send(msg)
        
        db.session.commit()
        
        return jsonify({'message': 'Invoice sent successfully!'})
    except Exception as e:
        return jsonify({'error': f'Error sending invoice: {str(e)}'}), 500 