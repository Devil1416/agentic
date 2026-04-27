from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize the Flask app
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Define the TodoItem model
class TodoItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    done = db.Column(db.Boolean, default=False)

# Create the database tables
with app.app_context():
    db.create_all()

@app.route('/todo', methods=['POST'])
def create_todo():
    data = request.get_json()
    new_item = TodoItem(title=data['title'], done=False)
    db.session.add(new_item)
    db.session.commit()
    return jsonify({'id': new_item.id, 'title': new_item.title, 'done': new_item.done}), 201

@app.route('/todo', methods=['GET'])
def get_all_todos():
    todos = TodoItem.query.all()
    return jsonify([{'id': todo.id, 'title': todo.title, 'done': todo.done} for todo in todos])

@app.route('/todo/<int:id>', methods=['GET'])
def get_single_todo(id):
    todo = TodoItem.query.get(id)
    if not todo:
        return jsonify({'message': 'Todo item not found'}), 404
    return jsonify({'id': todo.id, 'title': todo.title, 'done': todo.done})

@app.route('/todo/<int:id>', methods=['PUT'])
def update_single_todo(id):
    data = request.get_json()
    todo = TodoItem.query.get(id)
    if not todo:
        return jsonify({'message': 'Todo item not found'}), 404
    todo.title = data['title']
    todo.done = data['done']
    db.session.commit()
    return jsonify({'id': todo.id, 'title': todo.title, 'done': todo.done})

@app.route('/todo/<int:id>', methods=['DELETE'])
def delete_single_todo(id):
    todo = TodoItem.query.get(id)
    if not todo:
        return jsonify({'message': 'Todo item not found'}), 404
    db.session.delete(todo)
    db.session.commit()
    return jsonify({'message': 'Todo item deleted successfully!'})