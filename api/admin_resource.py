import data
from flask_restful import Resource
from flask import jsonify


class AdminResource(Resource):
    def get(self, user_id: int):
        if abort_if_users_not_found(user_id):
            return jsonify({'status': f"User {user_id} not found"})
        session = data.db_session.create_session()
        user = session.query(data.user.User).filter(data.user.User.user_id == user_id).first()  # type:ignore[call-arg]
        if user:
            user.role = 0
            session.commit()
            return jsonify({'status': f"User {user_id} added to admin group"})


def abort_if_users_not_found(user_id):
    session = data.db_session.create_session()
    users = session.query(data.user.User).filter(data.user.User.user_id == user_id).first()  # type:ignore[call-arg]
    if not users:
        return True
