// frontend/src/app.js
const BASE_URL = 'http://localhost:5000'; // Replace with your Flask API URL

class TodoApp {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.todoInput = this.container.querySelector('.new-todo');
    this.todoList = this.container.querySelector('.todo-list');
    this.bindEvents();
  }

  bindEvents() {
    document.addEventListener('DOMContentLoaded', () => {
      this.fetchTodos();
    });

    this.container.addEventListener('submit', (event) => {
      event.preventDefault();
      if (!this.todoInput.value.trim()) return;
      this.addTodo(this.todoInput.value);
      this.todoInput.value = '';
    });
  }

  fetchTodos() {
    fetch(`${BASE_URL}/api/todos`)
      .then((response) => response.json())
      .then((data) => {
        data.forEach((item) => this.addTodoItem(item));
      });
  }

  addTodo(text) {
    const todo = { text, completed: false };
    
    fetch(`${BASE_URL}/api/todos`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(todo)
    })
    .then((response) => response.json())
    .then(() => this.fetchTodos());
  }

  addTodoItem({ id, text, completed }) {
    const li = document.createElement('li');
    li.dataset.id = id;
    li.innerHTML = `
      <div class="view">
        <input class="toggle" type="checkbox" ${completed ? 'checked' : ''}>
        <label>${text}</label>
        <button class="destroy"></button>
      </div>
    `;
    this.todoList.append(li);
  }
}

new TodoApp('app');