// frontend/src/app.js
const BASE_URL = 'http://localhost:5000'; // replace with your Flask backend URL

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
    const res = await fetch(`${BASE_URL}/todos/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ text })
    });
    
    const todo = await res.json();
    this.renderTodo(todo);
  }
  
  renderTodo(todo) {
    const li = document.createElement('li');
    li.innerText = todo.text;
    
    // Add delete button
    const delButton = document.createElement('button');
    delButton.innerText = 'Delete';
    delButton.addEventListener('click', () => {
      this.deleteTodo(todo._id);
      li.remove();
    });
    
    // Add update button
    const updButton = document.createElement('button');
    updButton.innerText = 'Update';
    updButton.addEventListener('click', () => {
      this.updateTodo(todo._id);
    });
    
    li.appendChild(delButton);
    li.appendChild(updButton);
    this.list.appendChild(li);
  }
  
  async deleteTodo(id) {
    await fetch(`${BASE_URL}/todos/delete/${id}`, { method: 'DELETE' });
  }
  
  async updateTodo(id) {
    const text = prompt('Enter new todo');
    
    if (text !== null && text.trim() !== '') {
      await fetch(`${BASE_URL}/todos/update/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text })
      });
    }
  }
  
  async getTodos() {
    const res = await fetch(`${BASE_URL}/todos`);
    const todos = await res.json();
    
    this.list.innerHTML = ''; // clear the list
    
    for (let todo of todos) {
      this.renderTodo(todo);
    }
  }
}

const app = new App();
app.getTodos();