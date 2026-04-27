from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname('__file__'))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'crud.sqlite3')
db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    done = db.Column(db.Boolean)

@app.route('/todos', methods=['GET'])
def get_all():
    todos = Todo.query.all()
    output = []
    for todo in todos:
        data = {'id': todo.id, 'title': todo.title, 'done': todo.done}
        output.append(data)
    return jsonify({'todos': output})

@app.route('/todo', methods=['POST'])
def create():
    data = request.get_json()
    new_todo = Todo(title=data['title'], done=False)
    db.session.add(new_todo)
    db.session.commit()
    return jsonify({'id': new_todo.id})

@app.route('/todo/<id>', methods=['PUT'])
def update(id):
    todo = Todo.query.get(id)
    if not todo:
        return jsonify({'error': 'task not found'}), 404
    data = request.get_json()
    todo.title = data['title']
    db.session.commit()
    return jsonify({'success': True})

@app.route('/todo/<id>', methods=['DELETE'])
def delete(id):
    todo = Todo.query.get(id)
    if not todo:
        return jsonify({'error': 'task not found'}), 404
    db.session.delete(todo)
    db.session.commit()
    return jsonify({'success': True})