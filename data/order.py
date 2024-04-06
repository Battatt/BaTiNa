import sqlalchemy
import datetime
from sqlalchemy import orm
from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin


class Order(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'orders'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    seller = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    seller_id = orm.relationship('User')
    item = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("items.id"))
    item_id = orm.relationship('Item')
    start = sqlalchemy.Column(sqlalchemy.DateTime,
                              default=datetime.datetime.now())
    end = sqlalchemy.Column(sqlalchemy.DateTime,
                           default=datetime.datetime.now() + datetime.timedelta(days=2))
    is_finished = sqlalchemy.Column(sqlalchemy.Boolean, default=False)


