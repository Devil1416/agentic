from flask import Blueprint, request, jsonify
from backend.db.models import Todo
from backend.api.app import db

todo_routes = Blueprint('todo_routes', __name__)

@todo_routes.route('/todos/', methods=['GET'])
def get_all():
    todos = Todo.query.all()
    return jsonify([todo.serialize for todo in todos])

@todo_routes.route('/todos/', methods=['POST'])
def create():
    data = request.get_json()
    new_todo = Todo(content=data['content'], completed=False)
    db.session.add(new_todo)
    db.session.commit()
    return jsonify(new_todo.serialize), 201

@todo_routes.route('/todos/<int:id>', methods=['GET'])
def get_one(id):
    todo = Todo.query.get(id)
    if not todo:
        return jsonify({'message': 'Todo item not found'}), 404
    return jsonify(todo.serialize)

@todo_routes.route('/todos/<int:id>', methods=['PUT'])
def update(id):
    data = request.get_json()
    todo = Todo.query.get(id)
    if not todo:
        return jsonify({'message': 'Todo item not found'}), 404
    todo.content = data['content']
    db.session.commit()
    return jsonify(todo.serialize)

@todo_routes.route('/todos/<int:id>', methods=['DELETE'])
def delete(id):
    todo = Todo.query.get(id)
    if not todo:
        return jsonify({'message': 'Todo item not found'}), 404
    db.session.delete(todo)
    db.session.commit()
    return jsonify({'message': 'Todo item deleted successfully'})