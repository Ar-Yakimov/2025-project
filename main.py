from datetime import datetime, UTC
from os import environ

from flask import Flask, render_template, abort, redirect, session, request, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.update(SQLALCHEMY_DATABASE_URI=environ.get("DATABASE_URI"),
                  SECRET_KEY=environ.get("SECRET_KEY"),
                  SESSION_TYPE="filesystem",
                  SESSION_PERMANENT=False)
database = SQLAlchemy(app)


class Note(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    user_id = database.Column(database.Integer, database.ForeignKey('user.id'), nullable=False)
    title = database.Column(database.String(35), nullable=False)
    text = database.Column(database.Text, nullable=False)
    date = database.Column(database.DateTime, default=datetime.now(UTC))

    def __repr__(self):
        return f"<Note {self.id}>"


class User(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    login = database.Column(database.String(12), unique=True, nullable=False)
    password_hash = database.Column(database.String(120), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.id}>"


with app.app_context():
    database.create_all()

csp = {
    'default-src': r"'self'",
    'script-src': [
        r"'self'",
        'https://cdn.jsdelivr.net'
    ],
    'style-src': [
        r"'self'",
        'https://cdn.jsdelivr.net'
    ],
    'img-src': r"'self'",
    'object-src': r"'none'",
    'font-src': 'https://cdn.jsdelivr.net',
    'base-uri': r"'self'",
    'form-action': r"'self'",
    'frame-ancestors': r"'none'",
}

talisman = Talisman(app, content_security_policy=csp)


@app.route('/')
def index():
    return redirect("/sing-in")


@app.route('/create', methods=['GET', 'POST'])
def create_note():
    if 'user_id' not in session:
        abort(403)

    if request.method == "POST":
        title = request.form['title']
        text = request.form['text']
        user_id = session['user_id']
        new_note = Note(title=title, text=text, user_id=user_id)

        try:
            database.session.add(new_note)
            database.session.commit()
            return redirect(url_for('show_notes'))
        except Exception as error:
            return f"Произошла ошибка: {error}"
    else:
        return render_template("create.html")


@app.route("/notes")
def show_notes():
    if 'user_id' not in session:
        abort(403)

    user_id = session['user_id']
    notes = Note.query.filter_by(user_id=user_id).order_by(Note.date.desc()).all()
    return render_template("notes.html", notes=notes)


@app.route("/notes/<int:id>")
def read_note(id):
    if 'user_id' not in session:
        abort(403)

    note = database.session.get(Note, id)

    if note is None:
        abort(404)

    if note.user_id != session['user_id']:
        abort(403)

    return render_template("note_detailed.html", note=note)


@app.route("/notes/<int:id>/del")
def remove_note(id):
    if 'user_id' not in session:
        abort(403)

    note = database.session.get(Note, id)

    if note is None:
        abort(404)

    if note.user_id != session['user_id']:
        abort(403)

    try:
        database.session.delete(note)
        database.session.commit()
        return redirect(url_for('show_notes'))
    except Exception as error:
        return f"Произошла ошибка: {error}"


@app.route("/notes/<int:id>/upd", methods=["POST", "GET"])
def change_note(id):
    if 'user_id' not in session:
        abort(403)

    note = database.session.get(Note, id)

    if note is None:
        abort(404)

    if note.user_id != session['user_id']:
        abort(403)

    if request.method == "POST":
        try:
            note.title = request.form['title']
            note.text = request.form['text']
            database.session.commit()
            return redirect(url_for('show_notes'))
        except Exception as error:
            database.session.rollback()
            return f"Произошла ошибка: {error}"
    else:
        return render_template('update.html', note=note)


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        new_login = request.form["new_login"]
        new_password = request.form["new_password"]

        if database.session.query(User).filter_by(login=new_login).first():
            flash("Пользователь уже существует!")
            return redirect("register.html")
        else:
            try:
                new_user = User(login=new_login)
                new_user.set_password(new_password)
                database.session.add(new_user)
                database.session.commit()
                return redirect(url_for('templates/notes.html'))
            except Exception as error:
                return f"Произошла ошибка: {error}"
    else:
        return render_template("register.html")


@app.route("/sing-in", methods=["GET", "POST"])
def sing_in():
    if request.method == "POST":
        login = request.form["old_login"]
        password = request.form["old_password"]
        user = User.query.filter_by(login=login).first()

        if not user:
            flash("Неверный логин!")
            return redirect("/notes")

        if not user.check_password(password):
            flash("Неверный пароль!")
            return redirect("/")

        session['user_id'] = user.id
        return redirect("/notes")
    else:
        return render_template("index.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect("/")


@app.route("/profile")
def info():
    if 'user_id' not in session:
        abort(403)

    user_id = session['user_id']
    user = User.query.get(user_id)

    if user:
        return render_template("profile.html", user=user)
    else:
        flash("Пользователь не найден")
        return redirect(url_for("index"))


@app.errorhandler(403)
def forbidden(error):
    return "Ошибка 403: У вас нет доступа к этому url!"


@app.errorhandler(404)
def dont_exist(error):
    return "Ошибка 404: Данный url не существует!"
