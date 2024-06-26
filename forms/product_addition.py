from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import StringField, IntegerField, SubmitField, FileField, TextAreaField, BooleanField, SelectField
from wtforms.validators import DataRequired, NumberRange


class ItemForm(FlaskForm):
    name = StringField("Название товара", validators=[DataRequired()])
    description = TextAreaField("Описание товара")
    category = SelectField("Категория",
                           choices=['Telegram','Discord', 'Roblox', 'Steam', 'Other'])
    image = FileField("Изображение", validators=[FileAllowed(['jpg', 'png'])])
    price = IntegerField("Цена", validators=[DataRequired()])
    amount = IntegerField("Количество", validators=[DataRequired(), NumberRange(min=1, max=100000)])
    is_visible = BooleanField("Разрешить публичный доступ к товару")
    submit = SubmitField('Подтвердить')

