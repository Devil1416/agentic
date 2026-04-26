Here is a simple example of how you might structure your frontend/src/script.js file in JavaScript to handle all frontend logic: fetching tasks from the API, rendering the list, and handling user input. This code assumes that you have an existing HTML element with id "todo-list" where the todo items will be appended.

```javascript
// Fetching data from the API
fetch('http://localhost:5000/api/todos') // replace 'localhost' and '5000' with your Flask server address and port
  .then(response => response.json())
  .then(data => renderTodoList(data))
  .catch(error => console.log('Error:', error));

// Rendering the list
function renderTodoList(todos) {
  const todoList = document.getElementById('todo-list');
  
  todos.forEach(todo => {
    const li = document.createElement('li');
    
    if (todo.completed) {
      li.classList.add('completed');
    }
    
    li.textContent = todo.content;
    todoList.appendChild(li);
  });
}

// Handling user input
const form = document.getElementById('todo-form'); // replace 'todo-form' with your actual form id
form.addEventListener('submit', event => {
  event.preventDefault();
  
  const content = event.target['new-todo'].value;
  
  fetch('http://localhost:5000/api/todos', { // replace 'localhost' and '5000' with your Flask server address and port
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({content})
  })
  .then(response => response.json())
  .then(() => fetch('http://localhost:5000/api/todos') // replace 'localhost' and '5000' with your Flask server address and port
    .then(response => response.json())
    .then(data => renderTodoList(data)))
  .catch(error => console.log('Error:', error));
});
```
This code is a simple example, you might need to adjust it according to your needs and the structure of your API. For instance, if your Flask server runs on a different port or hostname, you will have to update the fetch URLs accordingly. Also, this script assumes that the 'content' property of each todo item is a string and that the 'completed' property indicates whether the todo item has been completed. These assumptions might not hold in your actual application.