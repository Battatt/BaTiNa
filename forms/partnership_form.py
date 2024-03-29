from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField
from wtforms.validators import DataRequired


class PartnershipShip(FlaskForm):
    passport = StringField("Паспорт", validators=[DataRequired()])
    bank_account = StringField("Реквизиты банковского счёта", validators=[DataRequired()])
    license_agree = BooleanField('Лицензия')
    submit = SubmitField('Подтвердить')
