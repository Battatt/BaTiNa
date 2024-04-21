from flask_wtf import FlaskForm
from wtforms import SubmitField, BooleanField, EmailField, StringField
from wtforms.validators import DataRequired, Email


class PurchaseForm(FlaskForm):
    email = EmailField('Адрес почты', validators=[DataRequired()])
    card_number = StringField('Номер карты')
    term = StringField('Срок действия')
    cvc = StringField('CVC')
    card_owner = StringField('Имя держателя')
    acceptation = BooleanField('Я согласен с пользовательским соглашением')
    submit = SubmitField('Войти')

