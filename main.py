from datetime import datetime

from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///data.db'
database = SQLAlchemy(app)
with app.app_context():
    database.create_all()


class Note(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    title = database.Column(database.String(35), nullable=False)
    text = database.Column(database.Text, nullable=False)
    date = database.Column(database.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Note {self.id}>"


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


if __name__ == "__main__":
    app.run(debug=True)
