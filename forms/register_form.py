from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField, EmailField, DateField, StringField, FileField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    avatar = FileField("Аватар профиля")
    banner = FileField("Фон профиля")
    email = EmailField('Адрес почты', validators=[DataRequired()])
    name = StringField("Имя пользователя", validators=[DataRequired()])
    birthday = DateField("Дата рождения (дд.мм.гггг)", format='%d.%m.%Y')
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')

