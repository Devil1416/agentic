from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'  # Set your database URI here
db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    completed = db.Column(db.Boolean, default=False)

@app.route('/todos', methods=['GET'])
def get_all_todos():
    todos = Todo.query.all()
    return jsonify([todo.serialize for todo in todos])

@app.route('/todos', methods=['POST'])
def create_todo():
    new_todo = Todo(title=request.json['title'], completed=False)
    db.session.add(new_todo)
    db.session.commit()
    return jsonify(new_todo.serialize), 201

@app.route('/todos/<int:id>', methods=['GET'])
def get_todo(id):
    todo = Todo.query.get(id)
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404
    return jsonify(todo.serialize)

@app.route('/todos/<int:id>', methods=['PUT'])
def update_todo(id):
    todo = Todo.query.get(id)
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404
    if 'title' in request.json:
        todo.title = request.json['title']
    if 'completed' in request.json:
        todo.completed = request<｜begin▁of▁sentence｜>.json['completed']
    db.session.commit()
    return jsonify(todo.serialize)

@app.route('/todos/<int:id>', methods=['DELETE'])
def delete_todo(id):
    todo = Todo.query.get(id)
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404
    db.session.delete(todo)
    db.session.commit()
    return jsonify({'result': True})

if __name__ == "__main__":
    app.run(debug=True)