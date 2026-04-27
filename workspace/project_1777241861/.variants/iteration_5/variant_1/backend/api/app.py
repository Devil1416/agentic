from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize Flask app
app = Flask(__name__)

# Load configuration from config file
app.config.from_pyfile('../config/settings.py')

# Initialize database connection
db = SQLAlchemy(app)

# Import Todo model for CRUD operations
from backend.db.models import Todo  # adjust the path according to your project structure

@app.route('/todos', methods=['GET'])
def get_all_todos():
    todos = Todo.query.all()
    return jsonify([todo.serialize for todo in todos])

@app.route('/todos', methods=['POST'])
def create_todo():
    data = request.get_json()
    new_todo = Todo(title=data['title'], description=data['description'])
    db.session.add(new_todo)
    db.session.commit()
    return jsonify(new_todo.serialize), 201

@app.route('/todos/<int:id>', methods=['GET'])
def get_todo(id):
    todo = Todo.query.get(id)
    if not todo:
        return jsonify({'message': 'Todo item not found'}), 404
    return jsonify(todo.serialize)

@app.route('/todos/<int:id>', methods=['PUT'])
def update_todo(id):
    data = request.get_json()
    todo = Todo.query.get(id)
    if not todo:
        return jsonify({'message': 'Todo item not found'}), 404
    todo.title = data['title']
    todo.description = data['description']
    db.session.commit()
    return jsonify(todo.serialize)

@app.route('/todos/<int:id>', methods=['DELETE'])
def delete_todo(id):
    todo = Todo.query.get(id)
    if not todo:
        return jsonify({'message': 'Todo item not found'}), 404
    db.session.delete(todo)
    db.session.commit()
    return jsonify({'message': 'Todo item deleted successfully'})

if __name__ == "__main__":
    app.run(debug=True, port=5000)