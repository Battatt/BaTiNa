from flask_wtf import FlaskForm
from wtforms import PasswordField, BooleanField, SubmitField, EmailField, DateField, StringField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    email = EmailField('E-mail', validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    address = StringField("Address")
    birthday = DateField("Birthday(Y-m-d)", format='%Y-%m-%d')
    password = PasswordField('Password', validators=[DataRequired()])
    secret_key = StringField("Staff Only")
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Login')
