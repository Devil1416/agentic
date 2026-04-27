from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize the Flask app
app = Flask(__name__)

# Load configuration from settings.py file
app.config.from_pyfile('../config/settings.py')

# Initialize SQLAlchemy
db = SQLAlchemy(app)

class TodoItemModel(db.Model):
    __tablename__ = 'todos'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String())
    done = db.Column(db.Boolean(), default=False)

@app.route('/api/tasks', methods=['GET'])
def get_all_tasks():
    tasks = TodoItemModel.query.all()
    return jsonify([task.serialize for task in tasks])

@app.route('/api/tasks', methods=['POST'])
def create_task():
    new_task = TodoItemModel(text=request.json['text'], done=False)
    db.session.add(new_task)
    db.session.commit()
    return jsonify(new_task.serialize), 201

@app.route('/api/tasks/<int:id>', methods=['GET'])
def get_task(id):
    task = TodoItemModel.query.get(id)
    if not task:
        return jsonify({'message': 'Task not found'}), 404
    return jsonify(task.serialize)

@app.route('/api/tasks/<int:id>', methods=['PUT'])
def update_task(id):
    task = TodoItemModel.query.get(id)
    if not task:
        return jsonify({'message': 'Task not found'}), 404
    
    task.text = request.json['text']
    db.session.commit()
    return jsonify(task.serialize)

@app.route('/api/tasks/<int:id>', methods=['DELETE'])
def delete_task(id):
    task = TodoItemModel.query.get(id)
    if not task:
        return jsonify({'message': 'Task not found'}), 404
    
    db.session.delete(task)
    db.session.commit()
    return jsonify({'result': 'success'})