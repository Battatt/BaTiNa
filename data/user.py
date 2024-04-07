import datetime
import sqlalchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    role = sqlalchemy.Column(sqlalchemy.String, default=1)  # 0-admin, 1-customer, 2-seller
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    birthday = sqlalchemy.Column(sqlalchemy.Date,
                                 default=datetime.date(1970, 1, 1).strftime("%d.%m.%Y"))
    address = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    post_office_address = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    ip = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String,
                              index=True, unique=True, nullable=True)
    profile_photo = sqlalchemy.Column(sqlalchemy.String, default="NULL")
    profile_banner = sqlalchemy.Column(sqlalchemy.String, default="NULL")
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    user_id = sqlalchemy.Column(sqlalchemy.BigInteger, nullable=True)

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)
