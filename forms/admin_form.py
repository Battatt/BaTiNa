from flask_wtf import FlaskForm
from wtforms import PasswordField, BooleanField, SubmitField, EmailField, DateField, StringField
from wtforms.validators import DataRequired


class AdminForm(FlaskForm):
    user_id = StringField('User_ID', validators=[DataRequired()])
    submit = SubmitField('Войти')
