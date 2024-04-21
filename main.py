from flask import Flask, render_template, redirect, abort, request, make_response, url_for
from flask_login import login_user, login_required, logout_user, LoginManager, current_user
from flask_restful import Api
from flask_limiter import Limiter, RequestLimit
from flask_limiter.util import get_remote_address
from flask_discord import DiscordOAuth2Session, requires_authorization, Unauthorized
from waitress import serve
from werkzeug.middleware.proxy_fix import ProxyFix
from api import user_resource
from api import item_resource
from api import validate_location
from data import db_session
from data.order import Order
from data.user import User
from data.item import Item
from forms.admin_application_form import AdminForm
from forms.product_addition import ItemForm
from forms.purchase_form import PurchaseForm
from forms.login_form import LoginForm
from forms.register_form import RegisterForm
from dotenv import load_dotenv
import requests
import jinja2
import base64
import random
import os
import logging


logger = logging.getLogger(__name__)


def default_error_responder(request_limit: RequestLimit):
    error_template = jinja2.Environment().from_string(
        """
    <h1>Breached rate limit of: {{request_limit.limit}}</h1>
    <h2>Path: {{request.path}}</h2>
    """
    )
    return make_response(render_template(error_template, request_limit=request_limit))


os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "true"  # !! Only in development environment.
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
app = Flask(__name__)  # python -m flask --app main run --debug
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)
limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri="memory://",
    on_breach=default_error_responder
)
HOST, PORT = "127.0.0.1", 5000
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config["DISCORD_CLIENT_ID"] = os.getenv("DISCORD_CLIENT_ID")
app.config["DISCORD_CLIENT_SECRET"] = os.getenv("DISCORD_CLIENT_SECRET")
app.config["DISCORD_REDIRECT_URI"] = f"http://{HOST}:{PORT}/oauth_callback"
app.config["DISCORD_BOT_TOKEN"] = os.getenv("DISCORD_BOT_TOKEN")
discord = DiscordOAuth2Session(app)
login_manager = LoginManager()
login_manager.init_app(app)
api_app = Api(app)
api_app.add_resource(user_resource.UserResource, '/api/profile/<int:user_id>')
api_app.add_resource(item_resource.ItemResource, '/api/item/<int:id>')
api_app.add_resource(item_resource.ItemListResource, '/api/items')
limiter.limit("1/second")(user_resource.UserResource)  # Don't work
api_app.add_resource(validate_location.GeoIpResource, '/api/geoip/<string:ip>')
admin_key = "123456"


@limiter.limit("5/second")
def check_ip():
    ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    if "," in ip:
        ip_response = requests.get(f'http://{HOST}:{PORT}/api/geoip/{ip.split(",")[0]}')
        if ip_response.status_code == 200:
            if ip_response.json().get("country", None) not in ["RU", None]:
                return abort(404)
    return


@limiter.limit("5/second")
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


def get_all_items():
    response = requests.get(f'http://{HOST}:{PORT}/api/items')
    if response.status_code == 200:
        data = response.json()
        return data
    return None


@app.route('/')
def index():
    check_ip()
    items = get_all_items()["items"] if get_all_items()["items"] else []
    navbar_data = get_navbar_data(current_user.user_id) if current_user.is_authenticated else None
    return render_template("index.html", title='Batina — интернет магазин', navbar_data=navbar_data, items=items)


@app.route("/product/<int:id>")
def product_page(item_id):
    check_ip()
    response = requests.get(f'http://{HOST}:{PORT}/api/item/{item_id}')
    if response.status_code == 200:
        data = response.json()
        item = dict()
        for key, value in data["user"].items():
            if key == "image":
                item[key] = base64.b64encode(bytes.fromhex(value)).decode('ascii')
            else:
                item[key] = value
    else:
        return abort(404)
    navbar_data = get_navbar_data(current_user.user_id) if current_user.is_authenticated else None
    if item:
        return render_template("product_page.html", title=item["name"], navbar_data=navbar_data,
                               item=item)
    else:
        abort(404)


@login_required
@app.route("/purchase/<int:id>", methods=['GET', 'POST'])
def purchase_form(item_id):
    check_ip()
    response = requests.get(f'http://{HOST}:{PORT}/api/item/{item_id}')
    if response.status_code == 200:
        data = response.json()
        item = dict()
        for key, value in data["user"].items():
            if key == "image":
                item[key] = base64.b64encode(bytes.fromhex(value)).decode('ascii')
            else:
                item[key] = value
    else:
        return abort(404)
    if item:
        form = PurchaseForm()
        if form.validate_on_submit():
            email = form.email.data
            acceptation = form.acceptation.data
            if acceptation:
                """Здесь должна быть проверка на то, что человек оплатил товар"""
                db_sess = db_session.create_session()
                items_table = db_sess.query(Item)
                current_item = items_table.filter(Item.id == item["id"])
                if current_item:
                    is_visible = False if item["amount"] - 1 == 0 else True
                    current_item.update({"amount": item["amount"] - 1, "is_visible": is_visible})
                else:
                    abort(404)
                order = Order(customer=current_user.user_id, content=item["content"])  # type: ignore[call-arg]
                db_sess.add(order)
                db_sess.commit()
                return redirect("/")
        return render_template("purchase_form.html", form=form, title=item["name"],
                               navbar_data=get_navbar_data(current_user.user_id),
                               item=item)
    else:
        abort(404)


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
    check_ip()
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
    check_ip()
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        user_table = db_sess.query(User)
        if user_table.filter(User.email == form.email.data).first():  # type: ignore[call-arg]
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
        while user_table.filter(User.user_id == (user_id := int.from_bytes(random.randbytes(4), "little"))).first():
            # type: ignore[call-arg]
            pass
        ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        user = User(
            name=form.name.data,  # type: ignore[call-arg]
            email=form.email.data,  # type: ignore[call-arg]
            birthday=form.birthday.data,  # type: ignore[call-arg]
            ip=ip.split(",")[0] if "," in ip else ip,  # type: ignore[call-arg]
            profile_photo=avatar,  # type: ignore[call-arg]
            profile_banner=banner,  # type: ignore[call-arg]
            user_id=user_id  # type: ignore[call-arg]
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route("/profile/<int:user_id>")
def profile(user_id):
    check_ip()
    response = requests.get(f'http://{HOST}:{PORT}/api/profile/{user_id}')
    navbar_data = get_navbar_data(current_user.user_id) if current_user.is_authenticated else None
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
    if current_user.user_id == user_id:
        if True:  # ДОБАВИТЬ ОБРАБОТКУ НЕЗАБРАННЫХ ТОВАРОВ
            pass
        response = requests.delete(f'http://{HOST}:{PORT}/api/profile/{user_id}')
        if response.status_code == 200 and "status" not in response.json():
            return redirect("/")
    return abort(401)


@app.route('/agree')
def agree():
    navbar_data = get_navbar_data(current_user.user_id) if current_user.is_authenticated else None
    return render_template("agree.html", title="Соглашение", navbar_data=navbar_data)


@app.route("/orders")
def orders():
    navbar_data = get_navbar_data(current_user.user_id) if current_user.is_authenticated else None
    return render_template("base.html", title="ЗАКАЗЫ", navbar_data=navbar_data)


@app.route("/contacts")
def contacts():
    navbar_data = get_navbar_data(current_user.user_id) if current_user.is_authenticated else None
    return render_template("contacts.html", title="КОНТАКТЫ", navbar_data=navbar_data)


@app.route("/admin_submission")
@requires_authorization
def admin_submission():
    form = AdminForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()  # type: ignore[call-arg]
        if True:
            pass
        return render_template('admin_application.html',
                               message="pass",
                               form=form)
    navbar_data = get_navbar_data(current_user.user_id) if current_user.is_authenticated else None
    return render_template("admin_application.html", title="Заявка на админа", navbar_data=navbar_data, form=form)


@app.route("/discord_login")
def discord_login():
    return discord.create_session()


@app.route("/oauth_callback")
def callback():
    discord.callback()
    return redirect(url_for(".admin_submission"))


@app.errorhandler(Unauthorized)
def redirect_unauthorized(e):
    return redirect(url_for("discord_login"))


@app.route("/me")
@requires_authorization
def me():
    user = discord.fetch_user()
    user.add_to_guild(1086655956399697980)
    print(user.to_json())
    print(user.locale)
    print(user.fetch_guilds())
    return f"""
    <html>
        <head>
            <title>{user.name}</title>
        </head>
        <body>
            <img src='{user.avatar_url}' />
        </body>
    </html>"""


@app.route("/my_products")
def my_products():
    navbar_data = get_navbar_data(current_user.user_id) if current_user.is_authenticated else None
    return render_template("products.html", title="Мои товары", navbar_data=navbar_data)


@login_required
@app.route("/add_products", methods=['GET', 'POST'])
def add_products():
    form = ItemForm()
    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data
        category = form.category.data
        price = form.price.data
        amount = form.amount.data
        image = form.image.data.read()
        content = form.content.data
        if not image:
            with open(f"static/img/profile/avatar_{random.choice(['red', 'green', 'blue'])}.jpg", "rb") as image:
                image = bytearray(image.read())
        adder_id = current_user.user_id
        is_visible = form.is_visible.data
        item = Item(
            name=name,  # type: ignore[call-arg]
            content=content,  # type: ignore[call-arg]
            seller_id=adder_id,  # type: ignore[call-arg]
            description=description,  # type: ignore[call-arg]
            category=category,  # type: ignore[call-arg]
            image=image,  # type: ignore[call-arg]
            amount=amount,  # type: ignore[call-arg]
            price=price,  # type: ignore[call-arg]
            is_visible=is_visible,  # type: ignore[call-arg]
        )
        db_sess = db_session.create_session()
        db_sess.add(item)
        db_sess.commit()
        return redirect("/")
    navbar_data = get_navbar_data(current_user.user_id) if current_user.is_authenticated else None
    return render_template("product_form.html", title="Мои товары", navbar_data=navbar_data, form=form)


@app.errorhandler(401)
def not_found_error(error):
    navbar_data = get_navbar_data(current_user.user_id) if current_user.is_authenticated else None
    return render_template('401.html', message=error.description, navbar_data=navbar_data), 401


@app.errorhandler(404)
def not_found_error(error):
    navbar_data = get_navbar_data(current_user.user_id) if current_user.is_authenticated else None
    return render_template('404.html', message=error.description, navbar_data=navbar_data), 404


@app.errorhandler(500)
def internal_error(error):
    navbar_data = get_navbar_data(current_user.user_id) if current_user.is_authenticated else None
    """
    db_sess = db_session.create_session()
    db_sess.rollback()"""
    return render_template('500.html', navbar_data=navbar_data), 500


def main():
    db_session.global_init("db/batina.db")
    limiter.init_app(app)
    serve(app, host="0.0.0.0", port=PORT, threads=10)  # default threads=4; for development use app.run(HOST, PORT)


if __name__ == '__main__':
    main()
