from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField
from wtforms.validators import DataRequired


class AdminForm(FlaskForm):
    discord_account = StringField("Discord аккаунт", validators=[DataRequired()])
    license_agree = BooleanField('Я прочитал(-а) условия ......', validators=[DataRequired()])
    submit = SubmitField('Подтвердить')
