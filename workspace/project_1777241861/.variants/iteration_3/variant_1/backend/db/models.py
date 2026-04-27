from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class TodoItemModel(db.Model):
    __tablename__ = 'todos'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(), nullable=False)
    completed = db.Column(db.Boolean, default=False)