from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'  # Use your own database URI here
db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    done = db.Column(db.Boolean, default=False)

@app.route('/todo', methods=['POST'])
def create_todo():
    data = request.get_json()
    new_todo = Todo(title=data['title'], done=data['done'])
    db.session.add(new_todo)
    db.session.commit()
    return jsonify({'id': new_todo.id}), 201

@app.route('/todo', methods=['GET'])
def get_all_todos():
    todos = Todo.query.all()
    return jsonify([{'id': todo.id, 'title': todo.title, 'done': todo.done} for todo in todos])

@app.route('/todo/<int:todo_id>', methods=['GET'])
def get_single_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404
    return jsonify({'title': todo.title, 'done': todo.done})

@app.route('/todo/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    data = request.get_json()
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404
    todo.title = data['title']
    todo.done = data['done']
    db.session.commit()
    return jsonify({'message': 'Todo updated successfully'})

@app.route('/todo/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404
    db.session.delete(todo)
    db.session.commit()
    return jsonify({'message': 'Todo deleted successfully'})

if __name__ == "__main__":
    app.run(debug=True)