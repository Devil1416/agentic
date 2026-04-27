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
    done = db.Column(db.Boolean, default=False)

# Create the database tables
with app.app_context():
    db.create_all()

@app.route('/todo', methods=['POST'])
def create_item():
    data = request.get_json()
    new_item = TodoItem(title=data['title'], done=False)
    db.session.add(new_item)
    db.session.commit()
    return jsonify({'id': new_item.id, 'title': new_item.title, 'done': new_item.done}), 201

@app.route('/todo', methods=['GET'])
def read_items():
    items = TodoItem.query.all()
    return jsonify([{'id': item.id, 'title': item.title, 'done': item.done} for item in items]), 200

@app.route('/todo/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    item = TodoItem.query.get(item_id)
    if not item:
        return jsonify({'message': 'Item not found'}), 404
    
    data = request.get_json()
    item.title = data['title']
    item.done = data['done']
    db.session.commit()
    return jsonify({'id': item.id, 'title': item.title, 'done': item.done}), 200

@app.route('/todo/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    item = TodoItem.query.get(item_id)
    if not item:
        return jsonify({'message': 'Item not found'}), 404
    
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Item deleted successfully!'}), 200

if __name__ == "__main__":
    app.run(debug=True)