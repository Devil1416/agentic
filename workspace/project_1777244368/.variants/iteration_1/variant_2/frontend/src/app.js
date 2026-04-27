// frontend/src/app.js
const baseURL = 'http://localhost:5000'; // Replace with your Flask API URL

class TodoApp {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.todos = [];
  }
  
  async fetchTodos() {
    const response = await fetch(`${baseURL}/api/todos`);
    if (response.ok) {
      this.todos = await response.json();
      this.renderTodos();
    } else {
      console.error('Failed to fetch todos:', response.statusText);
    }
  }
  
  async createTodo(title, description) {
    const data = { title, description };
    const options = { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) };
    const response = await fetch(`${baseURL}/api/todos`, options);
    if (response.ok) {
      this.todos.push(await response.json());
      this.renderTodos();
    } else {
      console.error('Failed to create todo:', response.statusText);
    }
  }
  
  async deleteTodo(id) {
    const options = { method: 'DELETE' };
    const response = await fetch(`${baseURL}/api/todos/${id}`, options);
    if (response.ok) {
      this.todos = this.todos.filter(todo => todo.id !== id);
      this.renderTodos();
    } else {
      console.error('Failed to delete todo:', response.statusText);
    }
  }
  
  renderTodos() {
    // Implement your own HTML rendering logic here based on the requirements of your project
  }
}