from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize the Flask application
app = Flask(__name__)

# Configure the database URI from an environment variable
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite')

# Initialize SQLAlchemy
db = SQLAlchemy(app)

class TodoItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(1024), nullable=False)

@app.route('/todos', methods=['GET'])
def get_all_todos():
    todos = TodoItem.query.all()
    return jsonify([todo.serialize for todo in todos])

@app.route('/todos/<int:id>', methods=['GET'])
def get_single_todo(id):
    todo = TodoItem.query.get(id)
    if todo is None:
        return jsonify({'message': 'Todo not found'}), 404
    return jsonify(todo.serialize)

@app.route('/todos', methods=['POST'])
def create_todo():
    data = request.get_json()
    new_todo = TodoItem(content=data['content'])
    db.session.add(new_todo)
    db.session.commit()
    return jsonify(new_todo.serialize), 201

@app.route('/todos/<int:id>', methods=['PUT'])
def update_todo(id):
    todo = TodoItem.query.get(id)
    if todo is None:
        return jsonify({'message': 'Todo not found'}), 404
    data = request.get_json()
    todo.content = data['content']
    db.session.commit()
    return jsonify(todo.serialize)

@app.route('/todos/<int:id>', methods=['DELETE'])
def delete_todo(id):
    todo = TodoItem.query.get(id)
    if todo is None:<｜begin▁of▁sentence｜>
        return jsonify({'message': 'Todo not found'}), 404
    db.session.delete(todo)
    db.session.commit()
    return jsonify({'message': 'Todo deleted successfully'})

if __name__ == "__main__":
    if os.environ.get('DATABASE_URL') is None:
        db.create_all()  # Create tables for local development
    app.run(debug=True)