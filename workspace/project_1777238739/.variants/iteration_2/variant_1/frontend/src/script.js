from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
db = SQLAlchemy(app)

class Todo(db.Model):  # Define the 'Todo' model
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)

@app.route('/todos', methods=['GET'])  # Define the GET endpoint for fetching all todos
def get_all_todos():
    todos = Todo.query.all()
    return jsonify([todo.serialize for todo in todos])

@app.route('/todos', methods=['POST'])  # Define the POST endpoint for creating a new todo
def create_todo():
    data = request.get_json()
    new_todo = Todo(content=data['content'], completed=False)
    db.session.add(new_todo)
    db.session.commit()
    return jsonify(new_todo.serialize), 201

@app.route('/todos/<int:id>', methods=['PUT'])  # Define the PUT endpoint for updating a todo
def update_todo(id):
    data = request.get_json()
    todo = Todo.query.get(id)
    if 'content' in data:
        todo.content = data['content']
    if 'completed' in data:
        todo.completed = data['completed']
    db.session.commit()
    return jsonify(todo.serialize), 200

@app.route('/todos/<int:id>', methods=['DELETE'])  # Define the DELETE endpoint for deleting a todo
def delete_todo(id):
    todo = Todo.query.get(id)
    db.session.delete(todo)
    db.session.commit()
    return jsonify({'message': 'Todo item deleted!'}), 200

if __name__ == "__main__":
    app.run(debug=True)