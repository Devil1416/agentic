from flask import Flask, SQLAlchemy

from config import settings

app = Flask(__name__)
db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    completed = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<Todo %r>' % self.title