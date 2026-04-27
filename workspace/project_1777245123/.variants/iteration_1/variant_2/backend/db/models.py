from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class TodoItem(db.Model):
    __tablename__ = 'todoitems'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(256), nullable=False)
    completed = db.Column(db.Boolean, default=False)