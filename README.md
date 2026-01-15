# 🌊 AquaCRM - Pressure Washing CRM

AquaCRM is a specialized Customer Relationship Management (CRM) system designed for pressure washing businesses. It streamlines client management, quoting, invoicing, and payment tracking in one modern interface.

## 🚀 Features

- **Client Management**: Track contact details, service history, and notes.
- **Smart Quotes**: Create professional quotes and send them directly to clients.
- **Automated Invoicing**: Convert quotes to invoices with a single click.
- **Payment Tracking**: Record and manage payments for completed services.
- **Email Integration**: Integrated email logging for all client communications.
- **Modern Dashboard**: High-level overview of business performance.

## 🛠️ Tech Stack

- **Backend**: Python (Flask)
- **Database**: SQLite with SQLAlchemy ORM
- **Migrations**: Flask-Migrate
- **Styling**: Vanilla CSS (Modern, Responsive Design)
- **Forms/Validation**: Flask-WTF, Email-Validator

## 📦 Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone https://github.com/cnichols1734/pressure_washing_crm.git
   cd pressure_washing_crm
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Mac/Linux
   # .venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**:
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your-secret-key
   MAIL_SERVER=smtp.googlemail.com
   MAIL_PORT=587
   MAIL_USE_TLS=true
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   MAIL_DEFAULT_SENDER=your-email@gmail.com
   ```

5. **Initialize Database**:
   ```bash
   flask db upgrade
   ```

6. **Run the application**:
   ```bash
   python app.py
   ```
   The app will be available at `http://localhost:5005`.

## 📄 License

This project is for private use by AquaCRM.