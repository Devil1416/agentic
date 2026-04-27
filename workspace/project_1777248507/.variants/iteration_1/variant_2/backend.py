from flask import Flask, request, jsonify
import os

app = Flask(__name__, static_folder='frontend', template_folder='templates')

# Sample data for the todos
TODOS = [{'id': 1, 'task': 'Learn Python'}, {'id': 2, 'task': 'Build a REST API'}]

@app.route('/api/todos', methods=['GET'])
def get_todos():
    return jsonify(TODOS), 200

@app.route('/api/todos/<int:id>', methods=['GET'])
def get_todo(id):
    for todo in TODOS:
        if todo['id'] == id:
            return jsonify(todo), 200
    return jsonify({'error': 'Todo not found'}), 404

@app.route('/api/todos', methods=['POST'])
def create_todo():
    new_todo = request.get_json()
    TODOS.append(new_todo)
    return jsonify(new_todo), 201

@app.route('/api/todos/<int:id>', methods=['PUT'])
def update_todo(id):
    updated_todo = request.get_json()
    for i, todo in enumerate(TODOS):
        if todo['id'] == id:
            TODOS[i] = updated_todo
            return jsonify(updated_todo), 200
    return jsonify({'error': 'Todo not found'}), 404

@app.route('/api/todos/<int:id>', methods=['DELETE'])
def delete_todo(id):
    for i, todo in enumerate(TODOS):
        if todo['id'] == id:
            del TODOS[i]
            return jsonify({'message': 'Todo deleted'}), 204
    return jsonify({'error': 'Todo not found'}), 404

if __name__ == "__main__":
    app.run(debug=True)