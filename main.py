from flask import Flask, render_template


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


@app.route('/')
@app.route('/<title>')
@app.route('/index/<title>')
def index(title="main"):
    return render_template("index.html", title=title)


if __name__ == '__main__':
    app.run(port=5000, host='127.0.0.1')
