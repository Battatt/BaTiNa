from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField
from wtforms.validators import DataRequired


class PartnershipShip(FlaskForm):
    number_passport = StringField("Номер паспорта", validators=[DataRequired()])
    seria_passport = StringField("Серия паспорта", validators=[DataRequired()])
    inn = StringField("ИНН", validators=[DataRequired()])
    bank_account = StringField("Реквизиты банковского счёта", validators=[DataRequired()])
    license_agree = BooleanField('Я согласен с пользовательским соглашением')
    submit = SubmitField('Подтвердить')

