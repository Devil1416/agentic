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

from db.models import TodoItem  # noqa: E402

@app.route('/todos', methods=['POST'])
def add_todo():
    data = request.get_json()
    new_todo = TodoItem(text=data['text'])
    db.session.add(new_todo)
    db.session.commit()
    return jsonify({'id': new_todo.id})

@app.route('/todos', methods=['GET'])
def get_all_todos():
    todos = TodoItem.query.all()
    return jsonify([{'id': todo.id, 'text': todo.text} for todo in todos])

@app.route('/todos/<int:todo_id>', methods=['GET'])
def get_single_todo(todo_id):
    todo = TodoItem.query.get(todo<｜begin▁of▁sentence｜>)
    return jsonify({'id': todo.id, 'text': todo.text})

@app.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    data = request.get_json()
    todo = TodoItem.query.filter_by(id=todo_id).first()
    todo.text = data['text']
    db.session.commit()
    return jsonify({'id': todo.id})

@app.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    TodoItem.query.filter_by(id=todo_id).delete()
    db.session.commit()
    return jsonify({'result': 'success'})