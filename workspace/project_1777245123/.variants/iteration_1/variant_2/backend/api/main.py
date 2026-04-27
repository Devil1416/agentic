from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize the Flask app
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
# Configure database URI from environment variable or default to a local sqlite instance
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or \
    'sqlite:///' + os.path.join(basedir, 'todo.db')
# Initialize SQLAlchemy with the Flask app
db = SQLAlchemy(app)

class TodoItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(256), nullable=False)
    completed = db.Column(db.Boolean, default=False)

@app.route('/todo', methods=['POST'])
def create():
    data = request.get_json()
    new_item = TodoItem(content=data['content'], completed=data['completed'])
    db.session.add(new_item)
    db.session.commit()
    return jsonify({'id': new_item.id, 'content': new_item.content, 'completed': new_item.completed}), 201

@app.route('/todo', methods=['GET'])
def read():
    items = TodoItem.query.all()
    return jsonify([{'id': item.id, 'content': item.content, 'completed': item.completed} for item in items])

@app.route('/todo/<int:item_id>', methods=['PUT'])
def update(item_id):
    item = TodoItem.query.get(item_id)
    if not item:
        return jsonify({'error': 'Not found'}), 404
    data = request.get_json()
    item.content = data['content']
    item.completed = data['completed']
    db.session.commit()
    return jsonify({'id': item.id, 'content': item.content, 'completed': item.completed})

@app.route('/todo/<int:item_id>', methods=['DELETE'])
def delete(item_id):
    item = TodoItem.query.get(item_id)
    if not item:
        return jsonify({'error': 'Not found'}), 404
    db.session.delete(item)
    db.session.commit()
    return '', 204