from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize the Flask app
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Define the TodoItem model
class TodoItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    completed = db.Column(db.Boolean, default=False)

# Create the database tables
with app.app_context():
    db.create_all()

@app.route('/todo', methods=['POST'])
def add_item():
    data = request.get_json()
    new_item = TodoItem(title=data['title'], completed=False)
    db.session.add(new_item)
    db.session.commit()
    return jsonify({'id': new_item.id})

@app.route('/todo', methods=['GET'])
def get_items():
    items = TodoItem.query.all()
    return jsonify([{'id': item.id, 'title': item.title, 'completed': item.completed} for item in items])

@app.route('/todo/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    data = request.get_json()
    item = TodoItem.query.get(item_id)
    if 'title' in data:
        item.title = data['title']
    if 'completed' in data:
        item.completed = data['completed']
    db.session.commit()
    return jsonify({'message': 'Item updated successfully'})

@app.route('/todo/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    item = TodoItem.query.get(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Item deleted successfully'})