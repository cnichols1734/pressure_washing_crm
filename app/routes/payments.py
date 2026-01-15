from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash
from datetime import datetime
from app import db
from app.models import Payment, Invoice
from flask_login import login_required

# Create two blueprints - one for API and one for web interface
api_bp = Blueprint('api_payments', __name__, url_prefix='/api/payments')
bp = Blueprint('payments', __name__, url_prefix='/payments')

# Web Interface Routes
@bp.route('/')
@login_required
def index():
    """Display list of payments."""
    page = request.args.get('page', 1, type=int)
    method = request.args.get('method')
    client = request.args.get('client')
    start_date = request.args.get('start_date')
    
    query = Payment.query.join(Invoice).join(Invoice.client)
    
    if method:
        query = query.filter(Payment.method == method)
    if client:
        query = query.filter(Invoice.client.name.ilike(f'%{client}%'))
    if start_date:
        query = query.filter(Payment.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    
    pagination = query.order_by(Payment.date.desc()).paginate(
        page=page, per_page=10, error_out=False)
    payments = pagination.items
    
    return render_template('payments/index.html', payments=payments, pagination=pagination)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new payment."""
    invoice_id = request.args.get('invoice_id', type=int)
    return_to = request.args.get('return_to')
    
    # If invoice_id is provided, check if it's already paid
    if invoice_id:
        invoice = Invoice.query.get_or_404(invoice_id)
        balance = invoice.calculate_balance()
        if balance <= 0:
            flash('This invoice is already paid in full.', 'info')
            return redirect(url_for('invoices.view', id=invoice_id))
    
    if request.method == 'POST':
        data = request.form.to_dict()
        return_to = data.get('return_to')
        
        # Create payment
        payment = Payment(
            invoice_id=data['invoice_id'],
            amount=float(data['amount']),
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            method=data['method'],
            reference=data.get('reference', ''),
            notes=data.get('notes', '')
        )
        
        db.session.add(payment)
        
        # Explicitly fetch the invoice
        invoice = Invoice.query.get(data['invoice_id'])
        db.session.flush()
        balance = invoice.calculate_balance()
        if balance <= 0:
            invoice.status = 'paid'
        else:
            invoice.status = 'sent'
        
        db.session.commit()
        
        flash('Payment recorded successfully.', 'success')
        
        # Redirect based on return_to parameter
        if return_to == 'invoice':
            return redirect(url_for('invoices.view', id=invoice.id))
        return redirect(url_for('payments.index'))
    
    # Get unpaid invoices for the dropdown
    invoices = Invoice.query.filter(Invoice.status != 'paid').order_by(Invoice.date_issued.desc()).all()
    
    return render_template('payments/form.html', invoices=invoices, invoice_id=invoice_id, return_to=return_to)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit a payment."""
    payment = Payment.query.get_or_404(id)
    
    if request.method == 'POST':
        data = request.form.to_dict()
        
        # Update payment fields
        payment.invoice_id = data['invoice_id']
        payment.amount = float(data['amount'])
        payment.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        payment.method = data['method']
        payment.reference = data.get('reference', '')
        payment.notes = data.get('notes', '')
        
        # Update invoice status
        invoice = payment.invoice
        db.session.flush()
        balance = invoice.calculate_balance()
        if balance <= 0:
            invoice.status = 'paid'
        else:
            invoice.status = 'sent'
        
        db.session.commit()
        
        flash('Payment updated successfully.', 'success')
        return redirect(url_for('payments.index'))
    
    # Get all invoices for the dropdown
    invoices = Invoice.query.order_by(Invoice.date_issued.desc()).all()
    return render_template('payments/form.html', payment=payment, invoices=invoices)

@bp.route('/<int:id>')
@login_required
def view(id):
    """View a specific payment."""
    payment = Payment.query.get_or_404(id)
    return render_template('payments/view.html', payment=payment)

# API Routes
@api_bp.route('/', methods=['GET'])
def get_payments():
    """Get all payments."""
    payments = Payment.query.all()
    return jsonify([{
        'id': payment.id,
        'invoice_id': payment.invoice_id,
        'amount': float(payment.amount),
        'date': payment.date,
        'method': payment.method,
        'notes': payment.notes
    } for payment in payments])

@api_bp.route('/<int:id>', methods=['GET'])
def get_payment(id):
    """Get a specific payment."""
    payment = Payment.query.get_or_404(id)
    return jsonify({
        'id': payment.id,
        'invoice_id': payment.invoice_id,
        'amount': float(payment.amount),
        'date': payment.date,
        'method': payment.method,
        'notes': payment.notes
    })

@api_bp.route('/', methods=['POST'])
def create_payment():
    """Create a new payment."""
    data = request.get_json() or {}
    
    # Check required fields
    required_fields = ['invoice_id', 'amount']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Verify invoice exists
    invoice = Invoice.query.get(data['invoice_id'])
    if not invoice:
        return jsonify({'error': 'Invoice not found'}), 404
    
    # Create payment
    payment = Payment(
        invoice_id=data['invoice_id'],
        amount=data['amount'],
        date=data.get('date', datetime.now().date()),
        method=data.get('method', ''),
        notes=data.get('notes', '')
    )
    
    db.session.add(payment)
    
    # Update invoice status if payment covers full amount
    db.session.flush()
    balance = invoice.calculate_balance()
    if balance <= 0:
        invoice.status = 'paid'
    else:
        invoice.status = 'sent'  # Ensure it's not in draft status
    
    db.session.commit()
    
    return jsonify({
        'id': payment.id,
        'invoice_id': payment.invoice_id,
        'amount': float(payment.amount),
        'date': payment.date,
        'method': payment.method,
        'notes': payment.notes
    }), 201

@api_bp.route('/<int:id>', methods=['PUT'])
def update_payment(id):
    """Update a payment."""
    payment = Payment.query.get_or_404(id)
    data = request.get_json() or {}
    
    # Update payment fields
    for field in ['amount', 'date', 'method', 'notes']:
        if field in data:
            setattr(payment, field, data[field])
    
    # Update invoice status based on payments
    invoice = payment.invoice
    db.session.flush()
    balance = invoice.calculate_balance()
    if balance <= 0:
        invoice.status = 'paid'
    else:
        invoice.status = 'sent'
    
    db.session.commit()
    
    return jsonify({
        'id': payment.id,
        'invoice_id': payment.invoice_id,
        'amount': float(payment.amount),
        'date': payment.date,
        'method': payment.method,
        'notes': payment.notes
    })

@api_bp.route('/<int:id>', methods=['DELETE'])
def delete_payment(id):
    """Delete a payment."""
    payment = Payment.query.get_or_404(id)
    invoice = payment.invoice
    
    db.session.delete(payment)
    
    # Update invoice status
    db.session.flush()
    balance = invoice.calculate_balance()
    if balance <= 0:
        invoice.status = 'paid'
    elif invoice.status == 'paid':
        invoice.status = 'sent'
    
    db.session.commit()
    
    return jsonify({'message': 'Payment deleted successfully'}) 