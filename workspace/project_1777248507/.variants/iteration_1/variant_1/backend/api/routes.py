from flask import Blueprint, request, jsonify
from backend.db.models import Todo
from backend.app import db

api = Blueprint('api', __name__)

@api.route('/api/todos', methods=['GET'])
def get_all_todos():
    todos = Todo.query.all()
    return jsonify([todo.serialize for todo in todos])

@api.route('/api/todos', methods=['POST'])
def create_todo():
    data = request.get_json()
    new_todo = Todo(title=data['title'], description=data['description'])
    db.session.add(new_todo)
    db.session.commit()
    return jsonify(new_todo.serialize), 201

@api.route('/api/todos/<int:id>', methods=['GET'])
def get_todo(id):
    todo = Todo.query.get(id)
    if not todo:
        return jsonify({'message': 'Todo not found'}), 404
    return jsonify(todo.serialize)

@api.route('/api/todos/<int:id>', methods=['PUT'])
def update_todo(id):
    data = request.get_json()
    todo = Todo.query.get(id)
    if not todo:
        return jsonify({'message': 'Todo not found'}), 404
    todo.title = data['title']
    todo.description = data['description']
    db.session.commit()
    return jsonify(todo.serialize)

@api.route('/api/todos/<int:id>', methods=['DELETE'])
def delete_todo(id):
    todo = Todo.query.get(id)
    if not todo:
        return jsonify({'message': 'Todo not found'}), 404
    db.session.delete(todo)
    db.session.commit()
    return jsonify({'message': 'Todo deleted successfully'})