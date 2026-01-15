from app import create_app, db
from app.models import Client, Quote, QuoteItem, Invoice, InvoiceItem, Payment, EmailLog, Service, User

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'Client': Client, 
        'Quote': Quote, 
        'QuoteItem': QuoteItem,
        'Invoice': Invoice, 
        'InvoiceItem': InvoiceItem,
        'Payment': Payment,
        'EmailLog': EmailLog,
        'Service': Service,
        'User': User
    }

if __name__ == '__main__':
    app.run(debug=True, port=5005, host='0.0.0.0')