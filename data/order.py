import sqlalchemy
import datetime
from sqlalchemy import orm
from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin


class Order(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'orders'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    customer = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.user_id"))
    customer_id = orm.relationship('User')
    item = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("items.id"))
    item_id = orm.relationship('Item')
    date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now())


