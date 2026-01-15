from flask import Blueprint, render_template
from app.models import Service
from flask_login import login_required

bp = Blueprint('services', __name__, url_prefix='/services')

@bp.route('/')
@login_required
def index():
    services = Service.query.all()
    return render_template('services/index.html', services=services) 