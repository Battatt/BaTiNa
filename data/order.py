import sqlalchemy
import datetime
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class Order(SqlAlchemyBase):
    __tablename__ = 'orders'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    client = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    client_id = orm.relationship('User')
    seller = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    seller_id = orm.relationship('User')
    item = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("items.id"))
    item_id = orm.relationship('Item')
    start = sqlalchemy.Column(sqlalchemy.DateTime,
                              default=datetime.datetime.now())
    end= sqlalchemy.Column(sqlalchemy.DateTime,
                           default=datetime.datetime.now() + datetime.timedelta(days=2))
    is_finished = sqlalchemy.Column(sqlalchemy.Boolean, default=False)


