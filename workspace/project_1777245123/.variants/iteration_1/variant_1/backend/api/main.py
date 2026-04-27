from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname('__file__'))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
db = SQLAlchemy(app)

class TodoItemModel(db.Model):
    __tablename__ = 'todos'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(), nullable=False)
    completed = db.Column(db.Boolean, default=False)

    def __init__(self, content, completed):
        self.content = content
        self.completed = completed

@app.route('/')
def index():
    return 'Hello World!'

@app.route('/todos', methods=['POST'])
def add_todo():
    data = request.get_json()
    new_item = TodoItemModel(content=data['content'], completed=False)
    db.session.add(new_item)
    db.session.commit()
    return jsonify({'message': 'Todo item added successfully!'})

@app.route('/todos', methods=['GET'])
def get_all_todos():
    todos = TodoItemModel.query.all()
    results = [
        {
            "id": todo.id,
            "content": todo.content,
            "completed": todo.completed
        } for todo in todos]
    return jsonify({"count": len(results), "todos": results})

@app.route('/todos/<int:todo_id>', methods=['GET'])
def get_one_todo(todo_id):
    todo = TodoItemModel.query.filter_by(id=todo_id).first()
    if not todo:
        return jsonify({'message': 'Todo item not found!'})
    else:
        todo_data = {
            "id": todo.id,
            "content": todo.content,
            "completed": todo.completed
        }
        return jsonify({"todo": todo_data})

@app.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    todo = TodoItemModel.query.filter_by(id=todo_id).first()
    if not todo:
        return jsonify({'message': 'Todo item not found!'})
    else:
        db.session.delete(todo)
        db.session.commit()
        return jsonify({'message': 'Todo item deleted successfully!'})

if __name__ == "__main__":
    app.run(debug=True)