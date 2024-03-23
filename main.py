from flask import Flask, render_template, redirect, request
from flask_login import login_user, login_required, logout_user, LoginManager, current_user
from flask_restful import Api
import requests
from data import db_session
from data.user import User
from forms.login_form import LoginForm
from forms.register_form import RegisterForm
from api import user_resource


app = Flask(__name__)
HOST, PORT = "127.0.0.1", 5000
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)
api = Api(app)
api.add_resource(user_resource.UserResource, '/api/profile/<int:user_id>')
admin_key = "123456"


@app.route('/')
@app.route('/<title>')
@app.route('/index/<title>')
def index(title="Batina — интернет-магазин"):
    return render_template("index.html", title=title)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
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
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            birthday=form.birthday.data,
            address=form.address.data,
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
        print(user_data)
        # Дальнейшие действия с данными пользователя
        return render_template("profile.html", title="Профиль",
                               user_data=user_data["user"], user_id=user_id)
    else:
        return "AAAAAAAAAAA"

def main():
    db_session.global_init("db/batina.db")
    app.run(port=PORT, host=HOST)


if __name__ == '__main__':
    main()
