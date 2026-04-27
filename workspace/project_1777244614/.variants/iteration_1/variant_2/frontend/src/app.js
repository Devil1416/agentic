// frontend/src/app.js
const API_URL = 'http://localhost:5000'; // replace with your Flask backend URL

class App {
  constructor() {
    this.initialize();
  }
  
  initialize() {
    this.form = document.getElementById('todo-form');
    this.input = document.getElementById('todo-input');
    this.list = document.getElementById('todo-list');
    
    this.form.addEventListener('submit', (event) => {
      event.preventDefault();
      
      if(this.input.value !== ''){
        this.addTodo(this.input.value);
        this.input.value = '';
      }
    });
  }
  
  async addTodo(text) {
    const res = await fetch(`${API_URL}/todos`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ text })
    });
    
    if (res.ok) {
      const todo = await res.json();
      this.renderTodo(todo);
    } else {
      throw new Error('Failed to add todo');
    }
  }
  
  renderTodo(todo) {
    const li = document.createElement('li');
    
    li.innerHTML = `
      <span>${todo.text}</span>
      <button data-id="${todo.id}">Delete</button>
    `;
    
    this.list.append(li);
  }
  
  async deleteTodo(id) {
    await fetch(`${API_URL}/todos/${id}`, { method: 'DELETE' });
    const li = document.querySelector(`[data-id="${id}"]`);
    li.remove();
  }
  
  async loadTodos() {
    const res = await fetch(`${API_URL}/todos`);
    
    if (res.ok) {
      const todos = await res.json();
      
      for(let todo of todos){
        this.renderTodo(todo);
      }
    } else {
      throw new Error('Failed to load todos');
    }
  }
}

const app = new App();
app.loadTodos();