from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, TelField, SelectField, DateField, TextAreaField, DecimalField
from wtforms.validators import DataRequired, Email, Optional, NumberRange

class ClientForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    phone = TelField('Phone', validators=[Optional()])
    address1 = StringField('Address Line 1', validators=[Optional()])
    address2 = StringField('Address Line 2', validators=[Optional()])
    city = StringField('City', validators=[Optional()])
    state = StringField('State', validators=[Optional()])
    zip_code = StringField('ZIP Code', validators=[Optional()])

class InvoiceForm(FlaskForm):
    client_id = SelectField('Client', coerce=int, validators=[DataRequired()])
    invoice_number = StringField('Invoice Number', validators=[DataRequired()])
    date_issued = DateField('Date Issued', validators=[DataRequired()])
    due_date = DateField('Due Date', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    subtotal = DecimalField('Subtotal', validators=[Optional(), NumberRange(min=0)])
    tax_rate = DecimalField('Tax Rate (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    tax_amount = DecimalField('Tax Amount', validators=[Optional(), NumberRange(min=0)])
    total = DecimalField('Total', validators=[DataRequired(), NumberRange(min=0)])
    status = SelectField('Status', choices=[
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue')
    ], validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])

class QuoteForm(FlaskForm):
    client_id = SelectField('Client', coerce=int, validators=[DataRequired()])
    date_created = DateField('Date Created', validators=[DataRequired()])
    valid_until = DateField('Valid Until', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired')
    ], validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()]) 