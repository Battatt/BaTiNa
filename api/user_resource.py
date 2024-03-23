from flask_restful import abort, Resource
import data
from flask import *


class UserResource(Resource):
    def get(self, user_id):
        abort_if_news_not_found(user_id)
        session = data.db_session.create_session()
        users = session.query(data.user.User).get(user_id)
        return jsonify({'user': users.to_dict(
            only=('name', 'birthday', 'role', 'address', 'email'))})

    def delete(self, user_id):
        abort_if_news_not_found(user_id)
        session = data.db_session.create_session()
        users = session.query(data.user.User).get(user_id)
        session.delete(users)
        session.commit()
        return jsonify({'success': 'OK'})


def abort_if_news_not_found(user_id):
    session = data.db_session.create_session()
    users = session.query(data.user.User).get(user_id)
    if not users:
        abort(404, message=f"User {user_id} not found")
