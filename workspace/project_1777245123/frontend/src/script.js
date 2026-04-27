// frontend/src/script.js

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('form');
    const input = document.getElementById('input');
    const todoList = document.getElementById('todo-list');
  
    // Fetch data from Flask API when the page loads
    fetch('/api/todos')
        .then(response => response.json())
        .then(data => {
            data.forEach((item) => renderTodoItem(item));
        });
  
    form.addEventListener('submit', (event) => {
        event.preventDefault();
      
        const item = input.value;
        if (!item) return; // If no text, do nothing
      
        fetch('/api/todos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ content: item })
        }).then(response => response.json())
          .then(data => {
              renderTodoItem(data);
              input.value = ''; // Clear the input field after adding a todo item
          });
    });
  
    function renderTodoItem({ id, content, completed }) {
        const li = document.createElement('li');
      
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = completed;
        checkbox.addEventListener('change', () => {
            fetch(`/api/todos/${id}`, { method: 'PUT' })
                .then(() => li.remove()); // Remove the item from the list when it is checked as completed
        });
      
        const button = document.createElement('button');
        button.textContent = 'Delete';
        button.addEventListener('click', () => {
            fetch(`/api/todos/${id}`, { method: 'DELETE' })
                .then(() => li.remove()); // Remove the item from the list when delete is clicked
        });
      
        li.appendChild(checkbox);
        li.appendChild(document.createTextNode(content));
        li.appendChild(button);
        todoList.appendChild(li);
    }
});