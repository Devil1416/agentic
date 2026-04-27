from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class TodoItemModel(db.Model):
    __tablename__ = 'todos'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)