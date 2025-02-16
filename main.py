from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, abort, flash
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///data.db'
app.config["SECRET_KEY"] = pass
database = SQLAlchemy(app)
with app.app_context():
    database.create_all()


class Note(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    user_id = database.Column(database.Integer, database.ForeignKey('user.id'), nullable=False)
    title = database.Column(database.String(35), nullable=False)
    text = database.Column(database.Text, nullable=False)
    date = database.Column(database.DateTime, default=datetime.utcnow)

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
    return render_template("index.html")


@app.route('/create', methods=['GET', 'POST'])
def create_note():
    if request.method == "GET":
        return render_template("create.html")
    else:
        title = request.form['title']
        text = request.form['text']

        new_note = Note(title=title, text=text)
        try:
            database.session.add(new_note)
            database.session.commit()
            return redirect('/notes')
        except Exception as error:
            return f"Произошла ошибка: {error}"


@app.route("/notes")
def show_notes():
    notes = Note.query.order_by(Note.date.desc()).all()
    return render_template("notes.html", notes=notes)


@app.route("/notes/<int:id>")
def read_note(id):
    note = database.session.get(Note, id)
    return render_template("note_detailed.html", note=note)


@app.route("/notes/<int:id>/del")
def remove_note(id):
    note = database.session.get(Note, id)

    try:
        database.session.delete(note)
        database.session.commit()
        return redirect("/notes")
    except Exception as error:
        return f"Произошла ошибка: {error}"


@app.route("/notes/<int:id>/upd", methods=["POST", "GET"])
def change_note(id):
    note = database.session.get(Note, id)
    if request.method == "POST":
        note.title = request.form['title']
        note.text = request.form['text']

        try:
            database.session.commit()
            return redirect('/notes')
        except Exception as error:
            return f"Произошла ошибка: {error}"
    else:
        return render_template("update.html", note=note)


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "GET":
        abort(403)
    else:
        new_login = request.form["login"]
        new_password = request.form["password"]

        if database.session.query(User).filter_by(login=new_login).all():
            flash("Пользователь уже существует!")
        else:
            try:
                new_user = User(login=new_login, password=User.set_password(new_password))
                database.session.add(new_user)
                database.session.commit()
            except Exception as error:
                return f"Произошла ошибка: {error}"
        return redirect("/")


@app.route("/sing-in", methods=["GET", "POST"])
def sing_in():
    if request.method == "GET":
        abort(403)
    else:
        login = request.form["login"]
        password = request.form["password"]

        if check := database.session.query(User).filter_by(login=login).first():
            if check.check_password(password):
                USER = check.id
            else:
                flash("Неверный пароль!")
        else:
            flash("Несуществующий логин!")

        return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
