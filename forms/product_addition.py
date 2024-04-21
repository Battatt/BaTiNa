from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, FileField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, NumberRange


class ItemForm(FlaskForm):
    name = StringField("Название товара", validators=[DataRequired()])
    description = TextAreaField("Описание товара")
    category = StringField("Категория")
    content = StringField("Содержание товара", validators=[DataRequired()])
    image = FileField("Изображение")
    price = IntegerField("Цена", validators=[DataRequired()])
    amount = IntegerField("Количество", validators=[DataRequired(), NumberRange(min=1, max=100000)])
    is_visible = BooleanField("Разрешить публичный доступ к товару")
    submit = SubmitField('Подтвердить')

