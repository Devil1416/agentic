from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from backend.db.models import Todo

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SECRET_KEY'] = 'super_secret_key'

api = Api(app)

class TodoResource(Resource):
    def get(self):
        todos = Todo.query.all()
        return jsonify([{'id': todo.id, 'title': todo.title} for todo in todos])

    def post(self):
        data = request.get_json()
        todo = Todo(title=data['title'])
        db.session.add(todo)
        db.session.commit()
        return jsonify({'id': todo.id}), 201

    def put(self, todo_id):
        todo = Todo.query.get(todo_id)
        data = request.get_json()
        todo.title = data['title']
        db.session.commit()
        return jsonify({'title': todo.title})

    def delete(self, todo_id):
        todo = Todo.query.get(todo_id)
        db.session.delete(todo)
        db.session.commit()
        return jsonify({'message': 'Deleted'})

api.add_resource(TodoResource, '/api/todos')

if __name__ == '__main__':
    from flask_sqlalchemy import SQLAlchemy
    db = SQLAlchemy(app)
    db.create_all()
    app.run(debug=True)