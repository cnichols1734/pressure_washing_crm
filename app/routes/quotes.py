from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash, make_response
from datetime import datetime, timedelta
from decimal import Decimal
from app import db
from app.models import Quote, QuoteItem, Client, Invoice, EmailLog
from flask_login import login_required
from app.forms import QuoteForm
from app import mail
from flask_mail import Message
from sqlalchemy.orm import joinedload

# API Blueprint (existing)
api_bp = Blueprint('api_quotes', __name__, url_prefix='/api/quotes')
# Web Blueprint (new)
bp = Blueprint('quotes', __name__, url_prefix='/quotes')

# Web Interface Routes
@bp.route('/')
@login_required
def index():
    quotes = Quote.query.order_by(Quote.date_created.desc()).all()
    return render_template('quotes/index.html', quotes=quotes)

@bp.route('/<int:id>')
@login_required
def view(id):
    quote = Quote.query.options(joinedload(Quote.invoice)).get_or_404(id)
    # Use the relationship instead of manual query for better reliability
    invoice = quote.invoice
    
    response = render_template('quotes/view.html', quote=quote, invoice=invoice)
    # Add cache-busting headers to ensure fresh data
    response = make_response(response)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@bp.route('/new', methods=['GET', 'POST'])
@login_required
def create():
    client_id = request.args.get('client_id', type=int)
    form = QuoteForm()
    clients = Client.query.order_by(Client.name).all()
    form.client_id.choices = [(c.id, c.name) for c in clients]
    if client_id:
        form.client_id.data = client_id
    
    if request.method == 'POST':
        # Generate quote number
        year = datetime.now().year
        last_quote = Quote.query.filter(Quote.quote_number.like(f'Q-{year}-%')).order_by(Quote.id.desc()).first()
        if last_quote:
            last_number = int(last_quote.quote_number.split('-')[-1])
            quote_number = f'Q-{year}-{last_number + 1:03d}'
        else:
            quote_number = f'Q-{year}-001'
        
        # Create quote with basic fields
        quote = Quote(
            client_id=request.form.get('client_id'),
            quote_number=quote_number,
            date_created=datetime.now().date(),  # Always use current date for new quotes
            valid_until=datetime.strptime(request.form.get('valid_until'), '%Y-%m-%d').date() if request.form.get('valid_until') else None,
            status=request.form.get('status', 'draft'),
            notes=request.form.get('notes', '')
        )
        db.session.add(quote)
        db.session.flush()  # Get quote ID for line items
        
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
                item = QuoteItem(
                    quote_id=quote.id,
                    description=description,
                    quantity=quantity,
                    unit_price=unit_price
                )
                item.calculate_line_total()
                db.session.add(item)
            
            i += 1
        
        # Calculate quote total
        db.session.flush()  # Ensure all items are saved
        quote.calculate_total()
        
        db.session.commit()
        flash('Quote created successfully.', 'success')
        return redirect(url_for('quotes.view', id=quote.id))
    
    return render_template('quotes/form.html', form=form, clients=clients, quote=None)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    quote = Quote.query.get_or_404(id)
    form = QuoteForm(obj=quote)
    clients = Client.query.order_by(Client.name).all()
    form.client_id.choices = [(c.id, c.name) for c in clients]
    
    if request.method == 'POST':
        # Update basic quote fields
        quote.client_id = request.form.get('client_id')
        quote.valid_until = datetime.strptime(request.form.get('valid_until'), '%Y-%m-%d').date() if request.form.get('valid_until') else None
        quote.status = request.form.get('status')
        quote.notes = request.form.get('notes')
        
        # Handle deleted items
        deleted_items = request.form.getlist('deleted_items[]')
        for item_id in deleted_items:
            item = QuoteItem.query.get(item_id)
            if item and item.quote_id == quote.id:
                db.session.delete(item)
        
        # Get existing items for updating
        existing_items = {item.id: item for item in quote.items}
        processed_item_ids = set()
        
        # Process line items from form
        i = 0
        while f'items[{i}][description]' in request.form:
            description = request.form.get(f'items[{i}][description]')
            quantity_str = request.form.get(f'items[{i}][quantity]')
            unit_price_str = request.form.get(f'items[{i}][unit_price]')
            item_id = request.form.get(f'items[{i}][id]')
            
            # Convert to Decimal to match database field types
            try:
                quantity = Decimal(quantity_str) if quantity_str else Decimal('0')
            except (ValueError, TypeError):
                quantity = Decimal('0')
            
            try:
                unit_price = Decimal(unit_price_str) if unit_price_str else Decimal('0')
            except (ValueError, TypeError):
                unit_price = Decimal('0')
            
            if description:  # Only process if description is provided
                if item_id and int(item_id) in existing_items:
                    # Update existing item
                    item = existing_items[int(item_id)]
                    item.description = description
                    item.quantity = quantity
                    item.unit_price = unit_price
                    item.calculate_line_total()
                    processed_item_ids.add(int(item_id))
                else:
                    # Create new item
                    item = QuoteItem(
                        quote_id=quote.id,
                        description=description,
                        quantity=quantity,
                        unit_price=unit_price
                    )
                    item.calculate_line_total()
                    db.session.add(item)
            
            i += 1
        
        # Remove items that weren't in the form submission (but weren't explicitly deleted)
        # This handles items that were removed from the form but not added to deleted_items
        for item_id, item in existing_items.items():
            if item_id not in processed_item_ids and str(item_id) not in deleted_items:
                # This item was in the original quote but not in the form, so it was removed
                db.session.delete(item)
        
        # Recalculate quote total
        db.session.flush()  # Ensure all changes are reflected
        quote.calculate_total()
        
        db.session.commit()
        flash('Quote updated successfully.', 'success')
        return redirect(url_for('quotes.view', id=quote.id))
    
    return render_template('quotes/form.html', form=form, clients=clients, quote=quote)

@bp.route('/<int:id>/send')
@login_required
def send(id):
    """Send quote to client via email."""
    quote = Quote.query.get_or_404(id)
    
    # Directly use the email function's internals
    try:
        # Get client and prepare basics
        client = Client.query.get(quote.client_id)
        if not client.email:
            flash('Client has no email address', 'error')
            return redirect(url_for('quotes.view', id=quote.id))
            
        # Create email content
        from datetime import datetime
        from app import mail, db
        from flask_mail import Message
        
        subject = f'Your Quote #{quote.quote_number} from Aquaforce Pressure Washing'
        custom_message = ""  # No custom message for direct sends
        
        # Professional HTML template matching invoice style
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
        
        # Save email log
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
        
        flash('Quote sent successfully!', 'success')
    except Exception as e:
        flash(f'Error sending quote: {str(e)}', 'error')
    
    return redirect(url_for('quotes.view', id=quote.id))

# API Routes
@api_bp.route('/', methods=['GET'])
def get_quotes():
    """Get all quotes."""
    quotes = Quote.query.all()
    return jsonify([{
        'id': quote.id,
        'client_id': quote.client_id,
        'client_name': quote.client.name,
        'quote_number': quote.quote_number,
        'date_created': quote.date_created,
        'valid_until': quote.valid_until,
        'status': quote.status,
        'notes': quote.notes,
        'total': float(quote.total) if quote.total else 0.0
    } for quote in quotes])

@api_bp.route('/<int:id>', methods=['GET'])
def get_quote(id):
    """Get a specific quote with its items."""
    quote = Quote.query.get_or_404(id)
    items = [{
        'id': item.id,
        'description': item.description,
        'quantity': float(item.quantity),
        'unit_price': float(item.unit_price),
        'line_total': float(item.line_total) if item.line_total else 0.0
    } for item in quote.items]
    return jsonify({
        'id': quote.id,
        'client_id': quote.client_id,
        'client_name': quote.client.name,
        'quote_number': quote.quote_number,
        'date_created': quote.date_created,
        'valid_until': quote.valid_until,
        'status': quote.status,
        'notes': quote.notes,
        'total': float(quote.total) if quote.total else 0.0,
        'items': items
    })

@api_bp.route('/', methods=['POST'])
def create_quote():
    """Create a new quote with items."""
    data = request.get_json() or {}

    # Check required fields
    if 'client_id' not in data:
        return jsonify({'error': 'Missing client_id'}), 400

    # Verify client exists
    client = Client.query.get(data['client_id'])
    if not client:
        return jsonify({'error': 'Client not found'}), 404

    # Generate quote number (format: Q-YYYY-NNN)
    year = datetime.now().year
    last_quote = Quote.query.filter(Quote.quote_number.like(f'Q-{year}-%')).order_by(Quote.id.desc()).first()
    if last_quote:
        last_number = int(last_quote.quote_number.split('-')[-1])
        quote_number = f'Q-{year}-{last_number + 1:03d}'
    else:
        quote_number = f'Q-{year}-001'

    # Parse date_created and valid_until as date objects
    date_created = data.get('date_created')
    if date_created and isinstance(date_created, str):
        date_created = datetime.strptime(date_created, '%Y-%m-%d').date()
    else:
        date_created = datetime.now().date()

    valid_until = data.get('valid_until')
    if valid_until and isinstance(valid_until, str):
        valid_until = datetime.strptime(valid_until, '%Y-%m-%d').date()
    else:
        valid_until = (datetime.now() + timedelta(days=30)).date()

    # Create quote
    quote = Quote(
        client_id=data['client_id'],
        quote_number=quote_number,
        date_created=date_created,
        valid_until=valid_until,
        status=data.get('status', 'draft'),
        notes=data.get('notes', '')
    )

    db.session.add(quote)
    db.session.flush()  # Get the quote ID

    # Add items if provided
    if 'items' in data and isinstance(data['items'], list):
        for item_data in data['items']:
            item = QuoteItem(
                quote_id=quote.id,
                description=item_data.get('description', ''),
                quantity=item_data.get('quantity', 1),
                unit_price=item_data.get('unit_price', 0)
            )
            item.calculate_line_total()
            db.session.add(item)

    # Calculate total
    db.session.flush()
    quote.calculate_total()

    db.session.commit()

    return jsonify({
        'id': quote.id,
        'client_id': quote.client_id,
        'quote_number': quote.quote_number,
        'date_created': quote.date_created,
        'valid_until': quote.valid_until,
        'status': quote.status,
        'notes': quote.notes,
        'total': float(quote.total) if quote.total else 0.0
    }), 201

@api_bp.route('/<int:id>', methods=['PUT'])
def update_quote(id):
    """Update a quote."""
    quote = Quote.query.get_or_404(id)
    data = request.get_json() or {}
    
    # Update quote fields
    for field in ['client_id', 'date_created', 'valid_until', 'status', 'notes']:
        if field in data:
            value = data[field]
            if field in ['date_created', 'valid_until'] and isinstance(value, str):
                value = datetime.strptime(value, '%Y-%m-%d').date()
            setattr(quote, field, value)
    
    # Update items if provided
    if 'items' in data and isinstance(data['items'], list):
        # First, get existing items
        existing_items = {item.id: item for item in quote.items}
        
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
                item = QuoteItem(
                    quote_id=quote.id,
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
    
    # Calculate total
    db.session.flush()
    quote.calculate_total()
    
    db.session.commit()
    
    return jsonify({
        'id': quote.id,
        'client_id': quote.client_id,
        'quote_number': quote.quote_number,
        'date_created': quote.date_created,
        'valid_until': quote.valid_until,
        'status': quote.status,
        'notes': quote.notes,
        'total': float(quote.total) if quote.total else 0.0
    })

@api_bp.route('/<int:id>', methods=['DELETE'])
def delete_quote(id):
    """Delete a quote."""
    quote = Quote.query.get_or_404(id)
    db.session.delete(quote)
    db.session.commit()
    
    return jsonify({'message': 'Quote deleted successfully'})

@api_bp.route('/<int:id>/send', methods=['POST'])
def send_quote_api(id):
    """Send quote to client via email (API endpoint)."""
    quote = Quote.query.get_or_404(id)
    data = request.get_json() or {}
    
    try:
        # Get client and prepare basics
        client = Client.query.get(quote.client_id)
        if not client.email:
            return jsonify({'error': 'Client has no email address'}), 400
            
        # Create email content
        subject = f'Your Quote #{quote.quote_number} from Aquaforce Pressure Washing'
        custom_message = data.get('message', '')
        
        # Professional HTML template matching invoice style
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
        
        # Save email log
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
        
        return jsonify({'message': 'Quote sent successfully!'})
    except Exception as e:
        return jsonify({'error': f'Error sending quote: {str(e)}'}), 500 