// frontend/src/app.js
const baseURL = 'http://localhost:5000'; // replace with your Flask API URL

class TodoApp {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.todoInput = container.querySelector('.new-todo');
        this.todoList = container.querySelector('.todo-list');
        
        // bind methods to the instance of TodoApp for event listeners
        this.addTodo = this.addTodo.bind(this);
    }
    
    async fetchTodos() {
        const response = await fetch(`${baseURL}/todos`);
        return await response.json();
    }
    
    addTodo(event) {
        event.preventDefault();
        
        if (this.todoInput.value.trim().length > 0) {
            const data = {text: this.todoInput.value};
            
            fetch(`${baseURL}/todos`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            })
            .then(() => this.clearInput());
        }
    }
    
    async deleteTodo(event) {
        const li = event.target;
        const todoId = li.getAttribute('data-todo-id');
        
        await fetch(`${baseURL}/todos/${todoId}`, {method: 'DELETE'});
        this.renderTodos();
    }
    
    clearInput() {
        this.todoInput.value = '';
    }
    
    renderTodos(todos) {
        // Clear the existing todo list
        while (this.todoList.firstChild) {
            this.todoList.removeChild(this.todoList.firstChild);
        }
        
        // Render new todos
        if (!todos) todos = await this.fetchTodos();
        todos.forEach(({id, text}) => {
            const li = document.createElement('li');
            
            li.innerHTML = `<div class="view"><label>${text}</label>`;
            li.setAttribute('data-todo-id', id);
            
            // Add delete button
            const delButton = document.createElement('button');
            delButton.classList.add('destroy');
            delButton.addEventListener('click', this.deleteTodo);
            li.append(delButton);
            
            this.todoList.appendChild(li);
        });
    }
    
    init() {
        document.querySelector('.new-todo').addEventListener('submit', this.addTodo);
        
        // Fetch and render todos on load
        this.renderTodos();
    }
}