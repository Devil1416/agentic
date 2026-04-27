// frontend/src/app.js

class TodoApp {
    constructor() {
        this.todoInput = document.getElementById('new-todo');
        this.addButton = document.getElementById('add-button');
        this.todoList = document.getElementById('todo-list');
        
        this.initialize();
    }
    
    initialize() {
        this.addButton.addEventListener('click', () => {
            const todoText = this.todoInput.value;
            
            if (todoText) {
                fetch('/api/todos', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({text: todoText})
                })
                .then(response => response.json())
                .then(() => this.fetchTodos());
                
                this.todoInput.value = '';
            }
        });
        
        this.fetchTodos();
    }
    
    fetchTodos() {
        fetch('/api/todos')
            .then(response => response.json())
            .then(data => this.renderTodos(data));
    }
    
    renderTodos(todos) {
        this.todoList.innerHTML = '';
        
        todos.forEach(({id, text}) => {
            const todoItem = document.createElement('div');
            
            todoItem.textContent = text;
            
            const deleteButton = document.createElement('button');
            deleteButton.textContent = 'Delete';
            deleteButton.addEventListener('click', () => this.deleteTodo(id));
            
            todoItem.appendChild(deleteButton);
            this.todoList.appendChild(todoItem);
        });
    }
    
    deleteTodo(id) {
        fetch(`/api/todos/${id}`, {method: 'DELETE'})
            .then(() => this.fetchTodos());
    }
}

new TodoApp();