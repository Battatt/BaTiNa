from flask import Flask, render_template, redirect, abort, request
from flask_login import login_user, login_required, logout_user, LoginManager, current_user
from flask_restful import Api
from data import db_session
from data.user import User
from forms.login_form import LoginForm
from forms.register_form import RegisterForm
from forms.partnership_form import PartnershipShip
from api import user_resource, validate_location
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
api.add_resource(validate_location.LocationResource, '/api/location/<string:address>')
api.add_resource(validate_location.GeoIpResource, '/api/geoip/<string:ip>')
api.add_resource(validate_location.PostOfficeResource, '/api/post_office/<string:postal_code>')
admin_key = "123456"


def get_navbar_data(user_id):
    response = requests.get(f'http://{HOST}:{PORT}/api/profile/{user_id}')
    if response.status_code == 200:
        user_data = response.json()
        navbar_data = dict()
        for key, value in user_data["user"].items():
            if not key.startswith("profile"):
                navbar_data[key] = value
            else:
                navbar_data[key] = base64.b64encode(bytes.fromhex(value)).decode('ascii')
        return navbar_data
    return None


@app.route('/')
def index():
    if current_user.is_authenticated:
        response = requests.get(f'http://{HOST}:{PORT}/api/profile/{current_user.id}')
        if response.status_code == 200:
            navbar_data = get_navbar_data(current_user.id)
            return render_template("index.html", navbar_data=navbar_data)
        else:
            abort(404)
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
        loc_response = requests.get(f'http://{HOST}:{PORT}/api/location/{form.address.data}')
        ip_response = requests.get(f'http://{HOST}:{PORT}/api/geoip/{request.remote_addr}')
        if loc_response.status_code == 200 and "status" not in loc_response.json() and \
            len(loc_response.json()["results"]) and ip_response.status_code == 200 and \
                "status" not in ip_response.json():  # If true, then the API worked properly
            loc_json, ip_json = loc_response.json(), ip_response.json()
            if loc_json["results"][0]["status"] >= 0.5 and \
                    (request.remote_addr == "127.0.0.1" or
                     loc_json["results"][0]["postcode"][:3] == ip_json["postcode"][:3]):
                address = loc_json["results"][0]["formatted_address"]
                post_resp = requests.get(f'http://{HOST}:{PORT}/api/post_office/{loc_json["results"][0]["postcode"]}')
                if post_resp.status_code == 200 and "status" not in post_resp.json():
                    post_office_address = post_resp.json()["address"]
                else:
                    post_office_address = address
            else:
                return render_template('register.html', title='Регистрация',
                                       form=form, message="Введен неккоректный адрес")
        else:
            return render_template('register.html', title='Регистрация',
                                   form=form, message="Произошла ошибка с проверкой адреса. Повторите позже")
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
            address=address,  # type: ignore[call-arg]
            post_office_address=post_office_address,  # type: ignore[call-arg]
            ip=request.remote_addr,  # type: ignore[call-arg]
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
    navbar_data = get_navbar_data(current_user.id) if current_user.is_authenticated else None
    if response.status_code == 200 and "status" not in response.json():
        user_data, user_dict = response.json(), dict()
        for key, value in user_data["user"].items():
            if not key.startswith("profile"):
                user_dict[key] = value
            else:
                user_dict[key] = base64.b64encode(bytes.fromhex(value)).decode('ascii')
        return render_template("profile.html", title="Профиль",
                               user_data=user_dict, user_id=user_id, navbar_data=navbar_data)
    else:
        abort(404)


@login_required
@app.route("/user_delete/<int:user_id>")
def delete_profile(user_id):
    if current_user.is_authenticated and current_user.id == user_id:
        if True:  # ДОБАВИТЬ ОБРАБОТКУ НЕЗАБРАННЫХ ТОВАРОВ
            pass
        response = requests.delete(f'http://{HOST}:{PORT}/api/profile/{user_id}')
        if response.status_code == 200 and "status" not in response.json():
            return redirect("/")
    return abort(401)


@app.route("/partnership", methods=['GET', 'POST'])
def partnership():
    form = PartnershipShip()
    if form.validate_on_submit():
        return redirect("/")
    navbar_data = get_navbar_data(current_user.id) if current_user.is_authenticated else None
    return render_template("partnership.html", title="ПАРТНЁРСТВО", form=form, navbar_data=navbar_data)


@app.route("/orders")
def orders():
    navbar_data = get_navbar_data(current_user.id) if current_user.is_authenticated else None
    return render_template("base.html", title="ЗАКАЗЫ", navbar_data=navbar_data)


@app.errorhandler(401)
def not_found_error(error):
    navbar_data = get_navbar_data(current_user.id) if current_user.is_authenticated else None
    return render_template('401.html', message=error.description, navbar_data=navbar_data), 401


@app.errorhandler(404)
def not_found_error(error):
    navbar_data = get_navbar_data(current_user.id) if current_user.is_authenticated else None
    return render_template('404.html', message=error.description, navbar_data=navbar_data), 404


@app.errorhandler(500)
def internal_error(error):
    navbar_data = get_navbar_data(current_user.id) if current_user.is_authenticated else None
    """
    db_sess = db_session.create_session()
    db_sess.rollback()"""
    return render_template('500.html', navbar_data=navbar_data), 500


def main():
    db_session.global_init("db/batina.db")
    app.run(port=PORT, host=HOST)


if __name__ == '__main__':
    main()
