from app import db

class Service(db.Model):
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    default_rate = db.Column(db.Numeric(10, 2), nullable=False)
    
    def __repr__(self):
        return f'<Service {self.name}>' 