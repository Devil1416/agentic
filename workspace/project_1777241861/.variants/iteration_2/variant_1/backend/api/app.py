from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize the Flask app
app = Flask(__name__)

# Load configuration from settings.py file
app.config.from_pyfile('../config/settings.py')

# Initialize the database connection
db = SQLAlchemy(app)

# Import models for creating tables in the database
from backend.db import models  # noqa: E402,F401

@app.route('/todo', methods=['POST'])
def create_task():
    data = request.get_json()
    new_task = models.Todo(title=data['title'], description=data['description'])
    db.session.add(new_task)
    db.session.commit()
    return jsonify({'message': 'New task created!'}), 201

@app.route('/todo', methods=['GET'])
def get_all_tasks():
    tasks = models.Todo.query.all()
    output = []
    for task in tasks:
        task_data = {'id': task.id, 'title': task.title, 'description': task.description}
        output.append(task_data)
    return jsonify({'tasks': output})

@app.route('/todo/<int:task_id>', methods=['GET'])
def get_one_task(task_id):
    task = models.Todo.query.get(task_id)
    if not task:
        return jsonify({'message': 'Task not found!'}), 404
    task_data = {'id': task.id, 'title': task.title, 'description': task.description}
    return jsonify({'task': task_data})

@app.route('/todo/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json()
    task = models.Todo.query.get(task_id)
    if not task:
        return jsonify({'message': 'Task not found!'}), 404
    task.title = data['title']
    task.description = data['description']
    db.session.commit()
    return jsonify({'message': 'Task updated!'})

@app.route('/todo/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = models.Todo.query.get(task_id)
    if not task:
        return jsonify({'message': 'Task not found!'}), 404
    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': 'Task deleted!'})

if __name__ == "__main__":
    app.run(debug=True, port=os.getenv('PORT', 5000))