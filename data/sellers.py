import sqlalchemy
from flask_login import UserMixin
from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin


class Seller(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'sellers'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    # user_id
    number_passport = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)  # Хэшировать?
    seria_passport = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    bank_account = sqlalchemy.Column(sqlalchemy.String, nullable=True)

