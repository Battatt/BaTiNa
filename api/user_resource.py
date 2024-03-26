from flask_restful import abort, Resource
from flask import jsonify
import data


class UserResource(Resource):
    def get(self, user_id):
        abort_if_users_not_found(user_id)
        session = data.db_session.create_session()
        users = session.get(data.user.User, user_id)
        return jsonify({'user': {'address': users.address, 'birthday': users.birthday, 'email': users.email,
                                 'name': users.name, 'role': users.role,
                                 'profile_photo': users.profile_photo.hex(),
                                 'profile_banner': users.profile_banner.hex()}})

    def delete(self, user_id):
        abort_if_users_not_found(user_id)
        session = data.db_session.create_session()
        users = session.get(data.user.User, user_id)
        session.delete(users)
        session.commit()
        return jsonify({'success': 'OK'})


def abort_if_users_not_found(user_id):
    session = data.db_session.create_session()
    users = session.get(data.user.User, user_id)
    if not users:
        abort(404, message=f"User {user_id} not found")
