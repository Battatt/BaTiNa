from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField
from wtforms.validators import DataRequired


class PartnershipShip(FlaskForm):
    passport = StringField("Passport", validators=[DataRequired()])
    bank_account = StringField("Bank Account", validators=[DataRequired()])
    license_agree = BooleanField('I Agree with license')
    submit = SubmitField('Become Partner')
