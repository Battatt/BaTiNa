import data
from flask_restful import Resource
from flask import jsonify


class UserResource(Resource):
    def get(self, user_id: int):
        if abort_if_users_not_found(user_id):
            return jsonify({'status': f"User {user_id} not found"})
        session = data.db_session.create_session()
        users = session.query(data.user.User).filter(data.user.User.user_id == user_id).first()  # type:ignore[call-arg]
        return jsonify({'user': {'address': users.address, 'birthday': users.birthday, 'email': users.email,
                                 'name': users.name, 'role': users.role, 'profile_photo': users.profile_photo.hex(),
                                 'profile_banner': users.profile_banner.hex(), 'user_id': user_id}})

    def delete(self, user_id: int):
        if abort_if_users_not_found(user_id):
            return jsonify({'status': f"User {user_id} not found"})
        session = data.db_session.create_session()
        users = session.query(data.user.User).filter(data.user.User.user_id == user_id).first()  # type:ignore[call-arg]
        session.delete(users)
        session.commit()
        return jsonify({'success': 'OK'})


def abort_if_users_not_found(user_id):
    session = data.db_session.create_session()
    users = session.query(data.user.User).filter(data.user.User.user_id == user_id).first()  # type:ignore[call-arg]
    if not users:
        return True
