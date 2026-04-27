// frontend/src/app.js
const baseURL = 'http://localhost:5000'; // Replace with your Flask API URL

class TodoApp {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.todoInput = this.container.querySelector('.new-todo');
    this.todoList = this.container.querySelector('.todo-list');
    this.bindEvents();
  }

  bindEvents() {
    // Bind events for new todo creation and deletion
    document.addEventListener('keypress', (event) => {
      if (event.key === 'Enter') {
        event.preventDefault();
        const text = this.todoInput.value;
        if (!text) return;
        this.createTodo(text);
      }
    });
  }

  async createTodo(text) {
    // Create a new todo item and add it to the list
    const response = await fetch(`${baseURL}/todos/new`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ text })
    });
    if (!response.ok) throw new Error(await response.text());
    const todo = await response.json();
    this.addTodoToList(todo);
  }

  addTodoToList(todo) {
    // Create a list item for the given todo and append it to the todo list
    const li = document.createElement('li');
    li.dataset.id = todo.id;
    li.innerHTML = `
      <div class="view">
        <input class="toggle" type="checkbox" ${todo.completed ? 'checked' : ''}>
        <label>${todo.text}</label>
        <button class="destroy"></button>
      </div>
    `;
    this.todoList.appendChild(li);
  }
}

// Initialize the app with a container element having id 'app'
new TodoApp('app');