from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, FileField, TextAreaField
from wtforms.validators import DataRequired


class ItemForm(FlaskForm):
    name = StringField("Название товара", validators=[DataRequired()])
    description = TextAreaField("Описание товара")
    category = StringField("Категория")
    image = FileField("Изображение")
    price = IntegerField("Цена", validators=[DataRequired()])
    amount = IntegerField("Количество", validators=[DataRequired()])
    submit = SubmitField('Подтвердить')

