from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash
from app import db
from app.models import Client
from app.forms import ClientForm
from flask_login import login_required

# Create two blueprints - one for API and one for web interface
api_bp = Blueprint('api_clients', __name__, url_prefix='/api/clients')
bp = Blueprint('clients', __name__, url_prefix='/clients')

# Web Interface Routes
@bp.route('/')
@login_required
def index():
    """Display list of clients."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Client.query
    if search:
        query = query.filter(Client.name.ilike(f'%{search}%'))
    
    pagination = query.order_by(Client.name).paginate(
        page=page, per_page=10, error_out=False)
    clients = pagination.items
    
    return render_template('clients/index.html', clients=clients, pagination=pagination)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new client."""
    form = ClientForm()
    if form.validate_on_submit():
        client = Client(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            address1=form.address1.data,
            address2=form.address2.data,
            city=form.city.data,
            state=form.state.data,
            zip_code=form.zip_code.data
        )
        
        db.session.add(client)
        db.session.commit()
        
        flash('Client created successfully.', 'success')
        return redirect(url_for('clients.index'))
    
    return render_template('clients/form.html', form=form)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit a client."""
    client = Client.query.get_or_404(id)
    form = ClientForm(obj=client)
    
    if form.validate_on_submit():
        client.name = form.name.data
        client.email = form.email.data
        client.phone = form.phone.data
        client.address1 = form.address1.data
        client.address2 = form.address2.data
        client.city = form.city.data
        client.state = form.state.data
        client.zip_code = form.zip_code.data
        
        db.session.commit()
        
        flash('Client updated successfully.', 'success')
        return redirect(url_for('clients.index'))
    
    return render_template('clients/form.html', form=form, client=client)

@bp.route('/<int:id>')
@login_required
def view(id):
    """View a specific client."""
    client = Client.query.get_or_404(id)
    return render_template('clients/view.html', client=client)

# API Routes
@api_bp.route('/', methods=['GET'])
def get_clients():
    """Get all clients."""
    clients = Client.query.all()
    return jsonify([{
        'id': client.id,
        'name': client.name,
        'email': client.email,
        'phone': client.phone,
        'address1': client.address1,
        'address2': client.address2,
        'city': client.city,
        'state': client.state,
        'zip_code': client.zip_code,
        'created_at': client.created_at,
        'updated_at': client.updated_at
    } for client in clients])

@api_bp.route('/<int:id>', methods=['GET'])
def get_client(id):
    """Get a specific client."""
    client = Client.query.get_or_404(id)
    return jsonify({
        'id': client.id,
        'name': client.name,
        'email': client.email,
        'phone': client.phone,
        'address1': client.address1,
        'address2': client.address2,
        'city': client.city,
        'state': client.state,
        'zip_code': client.zip_code,
        'created_at': client.created_at,
        'updated_at': client.updated_at
    })

@api_bp.route('/', methods=['POST'])
def create_client():
    """Create a new client."""
    data = request.get_json() or {}
    
    required_fields = ['name', 'email']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    client = Client(
        name=data['name'],
        email=data['email'],
        phone=data.get('phone', ''),
        address1=data.get('address1', ''),
        address2=data.get('address2', ''),
        city=data.get('city', ''),
        state=data.get('state', ''),
        zip_code=data.get('zip_code', '')
    )
    
    db.session.add(client)
    db.session.commit()
    
    return jsonify({
        'id': client.id,
        'name': client.name,
        'email': client.email,
        'phone': client.phone,
        'address1': client.address1,
        'address2': client.address2,
        'city': client.city,
        'state': client.state,
        'zip_code': client.zip_code,
        'created_at': client.created_at,
        'updated_at': client.updated_at
    }), 201

@api_bp.route('/<int:id>', methods=['PUT'])
def update_client(id):
    """Update a client."""
    client = Client.query.get_or_404(id)
    data = request.get_json() or {}
    
    # Update client fields
    for field in ['name', 'email', 'phone', 'address1', 'address2', 'city', 'state', 'zip_code']:
        if field in data:
            setattr(client, field, data[field])
    
    db.session.commit()
    
    return jsonify({
        'id': client.id,
        'name': client.name,
        'email': client.email,
        'phone': client.phone,
        'address1': client.address1,
        'address2': client.address2,
        'city': client.city,
        'state': client.state,
        'zip_code': client.zip_code,
        'created_at': client.created_at,
        'updated_at': client.updated_at
    })

@api_bp.route('/<int:id>', methods=['DELETE'])
def delete_client(id):
    """Delete a client."""
    client = Client.query.get_or_404(id)
    db.session.delete(client)
    db.session.commit()
    
    return jsonify({'message': 'Client deleted successfully'}) 