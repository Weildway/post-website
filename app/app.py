#!/usr/bin/env python3
from flask import Flask, g, session, request
from flask import redirect, url_for
from flask import render_template, flash
import functools
# безопасное хеширование: bcrypt с солью. Два одинаковых пароля в базе будут выгляеть по разному
from werkzeug.security import generate_password_hash, check_password_hash
from psycopg2.extras import DictCursor
from uuid import uuid4

# мама я не хочу писать фронт
from flask_bootstrap import Bootstrap
from forms import LoginForm, RegisterForm, CreateForm, UpdateForm, TrackingForm

from config import configure

app = Flask(__name__)
app = configure(app)
Bootstrap(app)

def get_db():
    if 'db' not in g:
        g.db = app.config['CONN_POOL'].getconn()
        g.db.autocommit = True
        g.cur = g.db.cursor(cursor_factory=DictCursor)
    return g.db, g.cur


@app.teardown_appcontext
def close_conn(e):
    cur = g.pop('cur', None)
    db = g.pop('db', None)
    if db is not None:
        cur.close()
        app.config['CONN_POOL'].putconn(db)


def login_required(f):
    @functools.wraps(f)
    def inner_handle(*args, **kwargs):
        if 'user_id' in session:
            return f(*args, **kwargs)
        abort(403)

    return inner_handle


def admin_required(f):
    @functools.wraps(f)
    def inner_handle(*args, **kwargs):
        if 'user_id' not in session:
            abort(403)
        if session['is_admin']:
            return f(*args, **kwargs)
        abort(401)

    return inner_handle


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if request.method == "POST" and form.validate_on_submit():
        username, password = form.username.data, form.password.data
        db, cur = get_db()
        cur.execute(
            "SELECT * FROM users WHERE username = %s;",
            (username,)
        )
        user = cur.fetchone()
        if user:
            flash("Register failed.", category="error")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(form.password.data)
        cur.execute(
            "INSERT INTO users(username, password, is_admin) VALUES (%s, %s, %s)",
            (username, hashed_password, False)
        )
        cur.close()
        flash("Register success.")
        return redirect(url_for("login"))

    return render_template("register_user.html", form=form)


@app.route('/login', methods=('GET', 'POST'))
def login():
    form = LoginForm()
    # проверяем, что данные были посланы в корректном виде (валидаторы из forms.py)
    if request.method == "POST" and form.validate_on_submit():
        username, password = form.username.data, form.password.data
        db, cur = get_db()
        cur.execute(
            "SELECT * FROM users WHERE username = %s;",
            (username,)
        )
        user = cur.fetchone()
        cur.close()
        # если юзер не существует или пароль неверный, возвращаем одинаковые ошибки
        # иначе будет возможность энумерации пользователей, это уязвимость
        if user is None:
            flash("Failed to log in.", category="error")
            return redirect(url_for("login"))

        if not check_password_hash(user["password"], password):
            flash("Failed to log in.", category="error")
            return redirect(url_for("login"))

        session.clear()
        session['user_id'] = user["id"]
        session['username'] = user["username"]
        session['is_admin'] = user["is_admin"]
        return redirect(url_for("index"))

    return render_template("login_user.html", form=form)


@app.route('/logout')
def logout():
    session.clear()
    flash("You have signed out.")
    return redirect(url_for('index'))


@app.route('/')
def index():
    if session.get("is_admin"):
        db, cur = get_db()
        cur.execute(
            "SELECT (SELECT COUNT(*) FROM users WHERE is_admin = False), \
            (SELECT COUNT(*) FROM packages), \
            (SELECT COUNT(*) FROM packages where delivered = True);"
        )
        users, orders, delivered = cur.fetchone()
        cur.close()
        return render_template('index.html', total_users=users, total_orders=orders, delivered_orders=delivered)

    return render_template('index.html')


@app.route('/profile')
@login_required
def profile():
    db, cur = get_db()
    cur.execute(
        "SELECT track, \
         (SELECT username FROM users WHERE id=sender_id) as sender,\
         (SELECT username FROM users WHERE id=receiver_id) as receiver,\
         sender_addr,\
         receiver_addr,\
         sender_index,\
         receiver_index,\
         TO_CHAR(send_date, 'DD-MM-YYYY:HH:MI:SS') as send_date,\
         TO_CHAR(update_time, 'DD-MM-YYYY:HH:MI:SS') as update_time,\
         pkg_status \
         FROM packages WHERE receiver_id = %s or sender_id=%s;",
         (session["user_id"],session["user_id"])
    )
    orders = cur.fetchall()
    cur.close()
    return render_template("profile.html", orders=orders)


@app.route('/admin/users')
@admin_required
def users():
    db, cur = get_db()
    cur.execute(
        "SELECT username,\
         TO_CHAR(register_date, 'DD-MM-YYYY') as register_date,\
         (SELECT COUNT(*) FROM packages where sender_id = id) AS packages,\
         (SELECT TO_CHAR(MAX(send_date), 'DD-MM-YYYY:HH:MI:SS') from packages where sender_id = id) AS last_pkg \
         FROM users WHERE is_admin = False;"
    )
    users = cur.fetchall()
    cur.close()
    return render_template("admin/users.html", users=users)


@app.route('/admin/orders')
@admin_required
def orders():
    db, cur = get_db()
    cur.execute(
        "SELECT track, \
         (SELECT username FROM users WHERE id=sender_id) as sender,\
         (SELECT username FROM users WHERE id=receiver_id) as receiver,\
         sender_addr,\
         receiver_addr,\
         sender_index,\
         receiver_index,\
         TO_CHAR(send_date, 'DD-MM-YYYY:HH:MI:SS') as send_date,\
         TO_CHAR(update_time, 'DD-MM-YYYY:HH:MI:SS') as update_time,\
         pkg_status \
         FROM packages;"
    )
    orders = cur.fetchall()
    cur.close()
    return render_template("admin/orders.html", orders=orders)


@app.route('/admin/order/<track>', methods=['GET', 'POST'])
@admin_required
def order(track):
    db, cur = get_db()
    form = UpdateForm()
    if request.method == "POST" and form.validate_on_submit():
        sender          = form.sender.data
        receiver        = form.receiver.data
        sender_index    = form.sender_index.data
        receiver_index  = form.receiver_index.data
        sender_addr     = form.sender_addr.data
        receiver_addr   = form.receiver_addr.data
        pkg_name        = form.pkg_name.data
        pkg_status      = form.pkg_status.data

        if sender == receiver:
            flash(f"Can't send package to yourself.", category="error")
            return redirect(url_for("order"))  

        db, cur = get_db()
        cur.execute(
            "SELECT * FROM users WHERE username = %s or username = %s;",
            (sender, receiver)
        )
        users = cur.fetchall()

        if len(users) == 0:
            flash(f"Users {sender} and {receiver} does not exists.", category="error")
            return redirect(url_for("order"))
        elif len(users) == 1:
            # так лучше, чем делать два запроса к бд
            flash(f"User {sender if sender != users[0]['username'] else receiver } does not exists.", category="error")
            return redirect(url_for("order"))    

        cur.execute(
            "UPDATE packages SET \
            sender_id       = (SELECT id FROM users WHERE username = %s), \
            receiver_id     = (SELECT id FROM users WHERE username = %s), \
            sender_index    = %s, \
            receiver_index  = %s, \
            sender_addr     = %s, \
            receiver_addr   = %s, \
            pkg_name        = %s, \
            pkg_status      = %s  \
            WHERE track     = %s;",
            (
                sender, receiver,
                sender_index, receiver_index,
                sender_addr, receiver_addr,
                pkg_name, pkg_status, track
            )
        )
        cur.close()
        flash(f"Package info updated")
        return redirect(url_for("order", track=track))

    cur.execute(
        "SELECT \
         (SELECT username FROM users WHERE id=sender_id) as sender,\
         (SELECT username FROM users WHERE id=receiver_id) as receiver,\
         sender_index,\
         receiver_index,\
         sender_addr,\
         receiver_addr,\
         pkg_name, \
         pkg_status \
         FROM packages WHERE track = %s;",
         (track,)
    )
    package = cur.fetchone()
    print(package)
    cur.close()
    if not package:
        flash(f"Order not found.", category="error")
        return redirect(url_for("orders"))

    form.sender.data = package['sender']
    form.receiver.data = package['receiver']
    form.sender_index.data = package['sender_index']
    form.receiver_index.data = package['receiver_index']
    form.sender_addr.data = package['sender_addr']
    form.receiver_addr.data = package['receiver_addr']
    form.pkg_name.data = package['pkg_name']
    form.pkg_status.data = package['pkg_status']
    return render_template("admin/order.html", track=track, form=form)


@app.route('/admin/create', methods=["GET", "POST"])
@admin_required
def create():
    form = CreateForm()
    if request.method == "POST" and form.validate_on_submit():
        sender          = form.sender.data
        receiver        = form.receiver.data
        sender_index    = form.sender_index.data
        receiver_index  = form.receiver_index.data
        sender_addr     = form.sender_addr.data
        receiver_addr   = form.receiver_addr.data
        pkg_name        = form.pkg_name.data

        if sender == receiver:
            flash(f"Can't send package to yourself.", category="error")
            return redirect(url_for("create"))  

        db, cur = get_db()
        cur.execute(
            "SELECT * FROM users WHERE username = %s or username = %s;",
            (sender, receiver)
        )
        users = cur.fetchall()

        if len(users) == 0:
            flash(f"Users {sender} and {receiver} does not exists.", category="error")
            return redirect(url_for("create"))
        elif len(users) == 1:
            # так лучше, чем делать два запроса к бд
            flash(f"User {sender if sender != users[0]['username'] else receiver } does not exists.", category="error")
            return redirect(url_for("create"))    

        track = str(uuid4())
        cur.execute(
            "INSERT INTO packages( \
                sender_id, receiver_id, \
                sender_index, receiver_index, \
                sender_addr, receiver_addr, \
                pkg_name, track, pkg_status) \
             VALUES ( \
                (SELECT id FROM users WHERE username = %s), \
                (SELECT id FROM users WHERE username = %s), \
                 %s, %s, \
                 %s, %s, \
                 %s, %s, \
                 'Created')",
            (
                sender, receiver,
                sender_index, receiver_index,
                sender_addr, receiver_addr,
                pkg_name, track
            )
        )
        cur.close()
        flash(f"Order track number is {track}")
        return redirect(url_for("create"))
        
    return render_template("admin/create.html", form=form)


@app.route('/track', methods=["GET", "POST"])
def track():
    form = TrackingForm()
    if request.method == "POST" and form.validate_on_submit():
        order_code = form.order_code.data
        db, cur = get_db()
        cur.execute(
            "SELECT \
            (SELECT username FROM users WHERE id=sender_id) as sender,\
            (SELECT username FROM users WHERE id=receiver_id) as receiver,\
            sender_addr,\
            receiver_addr,\
            sender_index,\
            receiver_index,\
            TO_CHAR(send_date, 'DD-MM-YYYY:HH:MI:SS') as send_date,\
            TO_CHAR(update_time, 'DD-MM-YYYY:HH:MI:SS') as update_time,\
            pkg_status \
            FROM packages where track = %s;",
            (order_code,)
        )
        order = cur.fetchone()
        cur.close()
        if order is None:
            flash("Order not found.", category="error")
            return redirect(url_for("track"))

        return render_template("track.html", order=order)
    return render_template("track.html", form=form)


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=1337)
