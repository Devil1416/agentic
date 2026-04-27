from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname('__file__'))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.todo')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    done = db.Column(db.Boolean, default=False)

@app.route('/todo', methods=['POST'])
def create():
    data = request.get_json()
    new_todo = Todo(title=data['title'], done=data['done'])
    db.session.add(new_todo)
    db.session.commit()
    return jsonify({'id': new_todo.id})

@app.route('/todo', methods=['GET'])
def read():
    todos = Todo.query.all()
    return jsonify([{'id': todo.id, 'title': todo.title, 'done': todo.done} for todo in todos])

@app.route('/todo/<int:id>', methods=['PUT'])
def update(id):
    data = request.get_json()
    Todo.query.filter_by(id=id).update({'title': data['title'], 'done': data['done']})
    db.session.commit()
    return jsonify({"success": True})

@app.route('/todo/<int:id>', methods=['DELETE'])
def delete(id):
    Todo.query.filter_by(id=id).delete()
    db.session.commit()
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True)