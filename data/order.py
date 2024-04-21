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
    name = sqlalchemy.Column(sqlalchemy.String, default="NAME")
    content = sqlalchemy.Column(sqlalchemy.String, default="CONTENT")
    date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now())
    is_finished = sqlalchemy.Column(sqlalchemy.Boolean, default=False)


