from flask import Flask, request, jsonify
from backend.db.models import Todo
from backend.api.app import db

todos_bp = Blueprint('todos', __name__)

@todos_bp.route('/todos', methods=['GET'])
def get_all_todos():
    todos = Todo.query.all()
    return jsonify([todo.serialize for todo in todos])

@todos_bp.route('/todos/<int:id>', methods=['GET'])
def get_single_todo(id):
    todo = Todo.query.get(id)
    if not todo:
        return jsonify({'message': 'Todo item not found'}), 404
    return jsonify(todo.serialize)

@todos_bp.route('/todos', methods=['POST'])
def create_todo():
    data = request.get_json()
    new_todo = Todo(content=data['content'], completed=False)
    db.session.add(new_todo)
    db.session.commit()
    return jsonify({'message': 'Todo item created', 'id': new_todo.id}), 201

@todos_bp.route('/todos/<int:id>', methods=['PUT'])
def update_todo(id):
    todo = Todo.query.get(id)
    if not todo:
        return jsonify({'message': 'Todo item not found'}), 404
    data = request.get_json()
    todo.content = data['content']
    db.session.commit()
    return jsonify({'message': 'Todo item updated'})

@todos_bp.route('/todos/<int:id>', methods=['DELETE'])
def delete_todo(id):
    todo = Todo.query.get(id)
    if not todo:
        return jsonify({'message': 'Todo item not found'}), 404
    db.session.delete(todo)
    db.session.commit()
    return jsonify({'message': 'Todo item deleted'})