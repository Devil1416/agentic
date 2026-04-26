from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)

@app.route('/todos', methods=['GET'])
def get_all_todos():
    todos = Todo.query.all()
    output = []
    for todo in todos:
        todo_data = {'id': todo.id, 'content': todo.content, 'completed': todo.completed}
        output.append(todo_data)
    return jsonify({'todos': output})

@app.route('/todos', methods=['POST'])
def add_new_todo():
    data = request.get_json()
    new_todo = Todo(content=data['content'])
    db.session.add(new_todo)
    db.session.commit()
    return jsonify({'message': 'New todo item created!'})

@app.route('/todos/<id>', methods=['PUT'])
def update_todo(id):
    todo = Todo.query.get(id)
    if not todo:
        return jsonify({'message': 'No todo found!'})
    data = request.get_json()
    todo.content = data['content']
    db.session.commit()
    return jsonify({'message': 'Todo item updated!'})

@app.route('/todos/<id>', methods=['DELETE'])
def delete_todo(id):
    todo = Todo.query.get(id)
    if not todo:
        return jsonify({'message': 'No todo found!'})
    db.session.delete(todo)
    db.session.commit()
    return jsonify({'message': 'Todo item deleted!'})