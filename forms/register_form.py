from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField, EmailField, DateField, StringField, FileField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    email = EmailField('E-mail', validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    address = StringField("Address")
    birthday = DateField("Birthday(Year-month-day)", format='%Y-%m-%d')
    password = PasswordField('Password', validators=[DataRequired()])
    password_again = PasswordField('Repeat Password', validators=[DataRequired()])
    submit = SubmitField('Register')

