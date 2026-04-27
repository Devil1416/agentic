from flask_sqlalchemy import SQLAlchemy
from sqlite3 import dbapi2 as sqlite3

db = SQLAlchemy()

class TodoItem(db.Model):
    __tablename__ = 'todos'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_completed = db.Column(db.Boolean, default=False)