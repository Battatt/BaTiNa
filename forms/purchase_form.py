from flask_wtf import FlaskForm
from wtforms import SubmitField, BooleanField, EmailField
from wtforms.validators import DataRequired, Email


class PurchaseForm(FlaskForm):
    email = EmailField('Адрес почты', validators=[DataRequired()])
    acceptation = BooleanField('Я согласен с пользовательским соглашением')
    submit = SubmitField('Войти')

