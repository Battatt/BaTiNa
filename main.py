from flask import Flask, render_template, redirect, abort
from flask_login import login_user, login_required, logout_user, LoginManager
from flask_restful import Api
from data import db_session
from data.user import User
from forms.login_form import LoginForm
from forms.register_form import RegisterForm
from api import user_resource
import requests
import base64
import random
import os
from dotenv import load_dotenv


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
app = Flask(__name__)  # python -m flask --app main run --debug
HOST, PORT = "127.0.0.1", 5000
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
login_manager = LoginManager()
login_manager.init_app(app)
api = Api(app)
api.add_resource(user_resource.UserResource, '/api/profile/<int:user_id>')
admin_key = "123456"


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/<title>')
@app.route('/index/<title>')
def other_page(title):
    return redirect("/")


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()  # type: ignore[call-arg]
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():  # type: ignore[call-arg]
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        avatar, banner = form.avatar.data.read(), form.banner.data.read()
        if not avatar:
            with open(f"static/img/profile/avatar_{random.choice(['red', 'green', 'blue'])}.jpg", "rb") as image:
                avatar = bytearray(image.read())
        if not banner:
            with open("static/img/profile/banner.jpg", "rb") as image:
                banner = bytearray(image.read())
        user = User(
            name=form.name.data,  # type: ignore[call-arg]
            email=form.email.data,  # type: ignore[call-arg]
            birthday=form.birthday.data,  # type: ignore[call-arg]
            address=form.address.data,  # type: ignore[call-arg]
            profile_photo=avatar,  # type: ignore[call-arg]
            profile_banner=banner  # type: ignore[call-arg]
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route("/profile/<int:user_id>")
def profile(user_id):
    response = requests.get(f'http://{HOST}:{PORT}/api/profile/{user_id}')
    if response.status_code == 200:
        user_data = response.json()
        user_dict = dict()
        for key, value in user_data["user"].items():
            if not key.startswith("profile"):
                user_dict[key] = value
            else:
                user_dict[key] = base64.b64encode(bytes.fromhex(value)).decode('ascii')
        return render_template("profile.html", title="Профиль",
                               user_data=user_dict, user_id=user_id)
    else:
        abort(404)


@login_required
@app.route("/user_delete/<int:user_id>")
def delete_profile(user_id):
    response = requests.delete(f'http://{HOST}:{PORT}/api/profile/{user_id}')
    if response.status_code == 200:
        return redirect("/")
    else:  # ДОБАВИТЬ ОБРАБОТКУ НЕЗАБРАННЫХ ТОВАРОВ
        abort(401)


@app.route("/partnership")
def partnership():
    return render_template("base.html", title="ПАРТНЕРСТВО")


@app.route("/orders")
def orders():
    return render_template("base.html", title="ЗАКАЗЫ")


def main():
    db_session.global_init("db/batina.db")
    app.run(port=PORT, host=HOST)


@app.errorhandler(404)  # Add 401.html Unauthorized
def not_found_error(error):
    return render_template('404.html', message=error.description), 404


@app.errorhandler(500)
def internal_error(error):
    db_sess = db_session.create_session()
    db_sess.rollback()
    return render_template('500.html'), 500


if __name__ == '__main__':
    main()
