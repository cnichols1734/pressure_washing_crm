from app import create_app, db

def deploy():
    """Run deployment tasks."""
    app = create_app()
    app.app_context().push()
    
    # Create database and tables
    db.create_all()

if __name__ == '__main__':
    deploy()
    print('Database has been initialized.') 