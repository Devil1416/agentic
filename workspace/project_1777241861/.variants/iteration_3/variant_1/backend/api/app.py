from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize the Flask app
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

# Setup database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'todo.db')
db = SQLAlchemy(app)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    done = db.Column(db.Boolean, default=False)

@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    new_task = Task(title=data['title'], done=data['done'])
    db.session.add(new_task)
    db.session.commit()
    return jsonify({'id': new_task.id}), 201

@app.route('/tasks', methods=['GET'])
def get_all_tasks():
    tasks = Task.query.all()
    return jsonify([task.serialize for task in tasks])

@app.route('/tasks/<int:id>', methods=['PUT'])
def update_task(id):
    data = request.get_json()
    task = Task.query.filter_by(id=id).first()
    if 'title' in data:
        task.title = data['title']
    if 'done' in data:
        task.done = data['done']
    db.session.commit()
    return jsonify({'message': 'Task updated successfully!'})

@app.route('/tasks/<int:id>', methods=['DELETE'])
def delete_task(id):
    Task.query.filter_by(id=id).delete()
    db.session.commit()
    return jsonify({'message': 'Task deleted successfully!'})

if __name__ == "__main__":
    app.run(debug=True)