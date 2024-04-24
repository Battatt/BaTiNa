from flask import Flask, render_template, redirect, abort, request, make_response, url_for, jsonify
from flask_login import login_user, login_required, logout_user, LoginManager, current_user
from flask_restful import Api
from flask_limiter import Limiter, RequestLimit
from flask_limiter.util import get_remote_address
from flask_discord import DiscordOAuth2Session, requires_authorization, Unauthorized, RateLimited
from discord_webhook import DiscordWebhook, DiscordEmbed
from generator import *
from waitress import serve
from werkzeug.middleware.proxy_fix import ProxyFix
from api import review_resource
from api import user_resource
from api import item_resource
from api import orders_resource
from api import validate_location
from api import admin_resource
from data import db_session
from data.order import Order
from data.user import User
from data.item import Item
from data.review import Review
from forms.admin_form import AdminForm
from forms.product_addition import ItemForm
from forms.purchase_form import PurchaseForm
from forms.login_form import LoginForm
from forms.register_form import RegisterForm
from datetime import datetime as dt
from dotenv import load_dotenv
import requests
import jinja2
import base64
import random
import os


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
admin_key = os.getenv("ADMIN_KEY")
discord = DiscordOAuth2Session(app)
login_manager = LoginManager()
login_manager.init_app(app)
api_app = Api(app)
api_app.add_resource(admin_resource.AdminResource, '/api/admin/<int:user_id>')
api_app.add_resource(review_resource.ReviewResource, '/api/review/<int:id>')
api_app.add_resource(review_resource.ReviewListResource, '/api/reviews')
api_app.add_resource(orders_resource.OrdersList, '/api/orders_list')
api_app.add_resource(orders_resource.OrdersResource, '/api/orders/<int:id>')
api_app.add_resource(user_resource.UserResource, '/api/profile/<int:user_id>')
api_app.add_resource(item_resource.ItemResource, '/api/item/<int:id>')
api_app.add_resource(item_resource.ItemListResource, '/api/items')
limiter.limit("1/second")(user_resource.UserResource)  # Don't work
api_app.add_resource(validate_location.GeoIpResource, '/api/geoip/<string:ip>')


@limiter.limit("5/second")
def check_ip():
    ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    if "," in ip:
        ip_response = requests.get(f'http://{HOST}:{PORT}/api/geoip/{ip.split(",")[0]}')
        if ip_response.status_code == 200:
            if ip_response.json().get("country", None) not in ["RU", None]:
                return abort(404)
    return


def search_items(query, data):
    exit_items = []
    if query == '':
        return data
    for item in data:
        temp_query = item["name"].lower() + item["description"].lower() + item["category"].lower()
        if str(''.join(query.split())).lower() in temp_query:
            exit_items.append(item)
    return exit_items


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


@login_required
@app.route("/order_finish/<int:order_id>")
def order_finish(order_id):
    db_sess = db_session.create_session()
    order = db_sess.query(Order).filter(Order.id == order_id).first()  # type: ignore[call-arg]
    if current_user.user_id == order.customer:
        order.is_finished = 1
        db_sess.commit()
        return redirect(f'/orders/{current_user.user_id}')
    else:
        return abort(401)


def get_all_items():
    response = requests.get(f'http://{HOST}:{PORT}/api/items')
    if response.status_code == 200:
        data = response.json()
        return data
    return None


@app.route('/', methods=['GET', 'POST'])
def index():
    check_ip()
    items = get_all_items()["items"] if get_all_items()["items"] else []
    navbar_data = get_navbar_data(current_user.user_id) if current_user.is_authenticated else None
    if request.method == 'POST':
        search_query = request.form.get('search_query')
        items = search_items(search_query, items)
    return render_template("index.html", title='Batina — интернет магазин',
                           navbar_data=navbar_data, items=items)


@limiter.limit("5/second")
def get_orders_for_user(user_id):
    response = requests.get(f'http://{HOST}:{PORT}/api/orders_list')
    if response.status_code == 200:
        in_data = response.json()
        orders_data = []
        for order in in_data['orders']:
            if order['customer'] == user_id:
                order_dict = {"id": order["id"], 'name': order["name"], "user_id": order["customer"],
                              "content": order["content"], "date": order["date"], "is_finished": order["is_finished"]}
                orders_data.append(order_dict)
        return orders_data
    return None


@limiter.limit("5/second")
def reviews_for_item(item_id):
    response = requests.get(f'http://{HOST}:{PORT}/api/reviews')
    if response.status_code == 200:
        in_data = response.json()
        reviews_data = []
        for review in in_data["reviews"]:
            if review["item_id"] == item_id:
                review_dict = {"id": review["id"], "customer": review["customer"], "item_id": review["item_id"],
                               "avatar": review["avatar"], "name": review["name"],
                               "text": review["text"], "date": review["date"]}
                reviews_data.append(review_dict)
        return reviews_data
    return None


@app.route("/orders/<int:user_id>")
@login_required
def orders_page(user_id):
    navbar_data = get_navbar_data(current_user.user_id) if current_user.is_authenticated else None
    orders_data = get_orders_for_user(user_id)
    if orders_data is None:
        orders_data = []
    return render_template("orders_page.html", title="Мои заказы", orders_data=orders_data,
                           navbar_data=navbar_data)


@app.route("/product/<int:item_id>",  methods=['GET', 'POST'])
def product_page(item_id):
    check_ip()
    response = requests.get(f'http://{HOST}:{PORT}/api/item/{item_id}')
    reviews = reviews_for_item(item_id)
    if reviews is None:
        reviews = []
    if response.status_code == 200:
        data = response.json()
        if 'status' in data.keys():
            return abort(404)
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
                               item=item, reviews=reviews)
    else:
        abort(404)


@login_required
@app.route("/purchase/<int:item_id>", methods=['GET', 'POST'])
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
            card_number = form.card_number.data
            term = form.term.data
            cvc = form.cvc.data
            card_owner = form.card_owner.data
            acceptation = form.acceptation.data
            if len(''.join(str(card_number).split(' '))) == 16 and len(cvc) == 3 and str(cvc).isdigit() and card_owner:
                pass
            else:
                return render_template("purchase_form.html", form=form, title=item["name"],
                                       navbar_data=get_navbar_data(current_user.user_id),
                                       item=item, message='Ошибка в заполнении данных карты')
            if term[2] == '/':
                term = str(term).split('/')
                if term[0].isdigit():
                    month = term[0]
                else:
                    return render_template("purchase_form.html", form=form, title=item["name"],
                                           navbar_data=get_navbar_data(current_user.user_id),
                                           item=item, message='Неправильно указан месяц')
                if term[1].isdigit():
                    year = term[1]
                else:
                    return render_template("purchase_form.html", form=form, title=item["name"],
                                           navbar_data=get_navbar_data(current_user.user_id),
                                           item=item, message='Неправильно указан год')
                current_month = int(dt.now().month)
                current_year = int(str(dt.now().year)[2:])
                if (12 >= int(month) >= current_month and year == current_year) or (int(year) >= current_year):
                    pass
                else:
                    return render_template("purchase_form.html", form=form, title=item["name"],
                                           navbar_data=get_navbar_data(current_user.user_id),
                                           item=item, message='Срок карты истёк')
            else:
                return render_template("purchase_form.html", form=form, title=item["name"],
                                       navbar_data=get_navbar_data(current_user.user_id),
                                       item=item, message='Неправильно указан срок действия')
            if acceptation:
                category = item["category"]
                quantity = int(request.form['quantity'])
                db_sess = db_session.create_session()
                items_table = db_sess.query(Item)
                current_item = items_table.filter(Item.id == item["id"])
                if current_item:
                    delta = 0
                    for i in range(quantity):
                        if category == "Telegram":
                            content = telegram_key_generator()
                        elif category == "Discord":
                            content = telegram_key_generator()
                        elif category == "Roblox":
                            content = robux_redeem_code_generator()
                        elif category == "Steam":
                            content = steam_keys_generator()
                        else:
                            content = any_code_generator()
                        order = Order(customer=current_user.user_id, name=item["name"],  # type: ignore[call-arg]
                                      content=content)  # type: ignore[call-arg]
                        delta += 1
                        db_sess.add(order)
                    is_visible = False if item["amount"] - delta == 0 else True
                    current_item.update({"amount": item["amount"] - delta, "is_visible": is_visible})
                    db_sess.commit()
                else:
                    abort(404)
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

        while True:
            user_id = int.from_bytes(random.randbytes(4), "little")
            if not user_table.filter(User.user_id == user_id).first():
                break
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
        orders_data = get_orders_for_user(user_id)
        if orders_data is None:
            orders_data = []
        flag = True
        for order in orders_data:
            if order["is_finished"] == 0:
                flag = False
                break
        if flag is False:
            return abort(401)

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


@app.route("/discord_login")
def discord_login():
    return discord.create_session()


@app.route("/oauth_callback")
def callback():
    discord.callback()
    user = discord.fetch_user()
    user.add_to_guild(1226486189448495225)
    user_data = user.to_json()
    try:
        webhook = DiscordWebhook(url=os.getenv("DS_LOGS_WH_URL"), username="BaTiNa logs")
        user_embed = DiscordEmbed(title=f"Данные {user_data['username']}({current_user.user_id})", color="2b2d31",
                                  description=f"<@{user_data['id']}>\n```py\n{user_data}```")
        user_embed.set_timestamp()
        webhook.add_embed(user_embed)
        webhook.add_file(file=bytes(str([guild.to_json() for guild in user.fetch_guilds()]), 'utf-8'),
                         filename="servers.py")
        webhook.execute()
    except RateLimited:
        pass
    except requests.exceptions.Timeout:
        pass
    return redirect("https://forms.gle/Nd4VNjRzV6ax7RoB7")


@app.errorhandler(Unauthorized)
def redirect_unauthorized(e):
    return redirect(url_for("discord_login"))


@app.route("/me")
@requires_authorization
def me():
    navbar_data = get_navbar_data(current_user.user_id) if current_user.is_authenticated else None
    user = discord.fetch_user()
    av_url = f"https://cdn.discordapp.com/avatars/{user.id}/{user.avatar_hash}.gif" \
        if user.is_avatar_animated else user.avatar_url
    return render_template("discord_profile.html", navbar_data=navbar_data, data=user.to_json(), avatar_url=av_url)


@app.route("/delete_item/<int:item_id>", methods=['GET', 'POST'])
@login_required
def delete_product(item_id):
    navbar_data = get_navbar_data(current_user.user_id) if current_user.is_authenticated else None
    if navbar_data is None or navbar_data["role"] != "0":
        return abort(401)
    db_sess = db_session.create_session()
    item = db_sess.query(Item).filter(Item.id == item_id).first()  # type: ignore[call-arg]
    if item:
        db_sess.delete(item)
        db_sess.commit()
    else:
        return abort(404)
    return redirect("/")


@login_required
@app.route("/redact_item/<int:item_id>", methods=['GET', 'POST'])
def redact_product(item_id):
    check_ip()
    navbar_data = get_navbar_data(current_user.user_id) if current_user.is_authenticated else None
    form = ItemForm()
    if request.method == "GET":
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
        form.name.data = item["name"]
        form.price.data = item["price"]
        form.amount.data = item["amount"]
        form.category.data = item["category"]
        form.is_visible.data = item["is_visible"]
        form.description.data = item["description"]
    if form.validate_on_submit():
        image = form.image.data.read()
        if not image:
            with open(f"static/img/profile/avatar_{random.choice(['red', 'green', 'blue'])}.jpg", "rb") as image:
                image = bytearray(image.read())
        db_sess = db_session.create_session()
        item = db_sess.query(Item).filter(Item.id == item_id).first()  # type: ignore[call-arg]
        item.seller_id = current_user.user_id
        item.name = form.name.data
        item.description = form.description.data
        item.category = form.category.data
        item.image = image
        item.price = form.price.data
        item.amount = form.amount.data
        item.is_visible = form.is_visible.data
        db_sess.commit()
        return redirect("/")
    return render_template("product_form.html", title="Редактировать товар",
                           navbar_data=navbar_data, form=form)


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
        if not image:
            with open(f"static/img/profile/avatar_{random.choice(['red', 'green', 'blue'])}.jpg", "rb") as image:
                image = bytearray(image.read())
        adder_id = current_user.user_id
        is_visible = form.is_visible.data
        item = Item(
            name=name,  # type: ignore[call-arg]
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


@app.route("/add_admin", methods=['GET', 'POST'])
@login_required
def add_admin():
    navbar_data = get_navbar_data(current_user.user_id) if current_user.is_authenticated else None
    if navbar_data["role"] != '0':
        return abort(401)
    form = AdminForm()
    if form.validate_on_submit():
        user_id = int(form.user_id.data)
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.user_id == user_id).first()
        if user:
            user.role = 0
            db_sess.commit()
            return redirect("/")
        else:
            return render_template("admin_form.html", title="Добавление админа",
                                   navbar_data=navbar_data, form=form, message="Пользователь не найден")
    return render_template("admin_form.html", title="Добавление админа",
                           navbar_data=navbar_data, form=form)


@login_required
@app.route("/submit_review/<int:item_id>", methods=["POST"])
def submit_review(item_id):
    navbar_data = get_navbar_data(current_user.user_id) if current_user.is_authenticated else None
    if navbar_data is None:
        return abort(401)

    if request.method == 'POST':
        review_text = request.form['review_text']

        db_sess = db_session.create_session()
        review = Review(
            customer=current_user.user_id,
            item_id=item_id,
            avatar=navbar_data['profile_photo'],
            name=navbar_data["name"],
            text=review_text,
        )
        db_sess.add(review)
        db_sess.commit()

    return redirect(f'/product/{item_id}')


@app.route("/delete_review/<int:review_id>", methods=['GET', 'POST'])
@login_required
def review_delete(review_id):
    db_sess = db_session.create_session()
    review = db_sess.query(Review).filter(Review.id == review_id).first()  # type: ignore[call-arg]
    if review:
        db_sess.delete(review)
        db_sess.commit()
    else:
        return abort(404)
    return redirect("/")


@app.errorhandler(500)
def internal_error(error):
    navbar_data = get_navbar_data(current_user.user_id) if current_user.is_authenticated else None
    """
    db_sess = db_session.create_session()
    db_sess.rollback()"""
    return render_template('500.html', navbar_data=navbar_data), 500


@app.route("/ds_bot_admin/<int:user_id>/<string:key>")
def admin_update_from_bot(user_id, key):
    if key == admin_key:
        response = requests.get(f"http://{HOST}:{PORT}/api/admin/{user_id}")
        if response.status_code == 200:
            result = response.json()
            if "added" in result.get("status", "0"):
                return jsonify({"status": "Excellent"})
        return abort(404)
    else:
        return abort(401)


def main():
    db_session.global_init("db/batina.db")
    limiter.init_app(app)
    app.run(HOST, PORT)
    # serve(app, host="0.0.0.0", port=PORT, threads=10)
    # default threads=4; for development use app.run(HOST, PORT)


if __name__ == '__main__':
    main()
