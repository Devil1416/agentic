// frontend/src/app.js
const baseURL = 'http://localhost:5000'; // replace with your Flask API URL

class TodoApp {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.todoInput = null;
        this.todoList = [];
    }

    init() {
        this.render();
        this.attachEventListeners();
    }

    render() {
        // clear the container
        this.container.innerHTML = '';
        
        // create input for new todo item
        const div = document.createElement('div');
        this.todoInput = document.createElement('input');
        this.todoInput.type = 'text';
        this.todoInput.placeholder = 'New task...';
        div.appendChild(this.todoInput);
        
        // create button for adding new todo item
        const addButton = document.createElement('button');
        addButton.innerHTML = 'Add Task';
        addButton.addEventListener('click', () => this.addTodo());
        div.appendChild(addButton);
        
        // append the input and button to the container
        this.container.appendChild(div);
    }

    attachEventListeners() {
        document.body.addEventListener('keypress', (event) => {
            if (event.code === 'Enter') {
                event.preventDefault();
                this.addTodo();
            }
        });
    }

    async addTodo() {
        const todoText = this.todoInput.value.trim();
        if (!todoText) return;
        
        // create new todo item and send POST request to Flask API
        const response = await fetch(`${baseURL}/api/todos`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({text: todoText})
        });
        
        // update the local todo list and rerender the UI
        this.todoList = await response.json();
        this.render();
    }
}

const app = new TodoApp('app');
app.init();