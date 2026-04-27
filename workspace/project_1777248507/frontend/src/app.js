Based on the provided project plan and interface contract, here is a raw source code for frontend/src/app.js:

```javascript
// frontend/src/app.js
const apiBase = "http://localhost:5000";
const todoListId = ""; // Add your HTML id here

window.onload = function() {
    fetch(apiBase + "/api/todos")
        .then((response) => response.json())
        .then((data) => renderTodoList(data))
        .catch((error) => console.log('Error:', error));
};

function addTodo() {
    const title = document.getElementById("new-todo").value;
    fetch(apiBase + "/api/todos", {
        method: "POST",
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({title: title})
    })
    .then((response) => response.json())
    .then((data) => renderTodo(data))
    .catch((error) => console.log('Error:', error));
}

function deleteTodo(id) {
    fetch(apiBase + "/api/todos/" + id, {method: "DELETE"})
        .then(() => fetch(apiBase + "/api/todos")
            .then((response) => response.json())
            .then((data) => renderTodoList(data))
            .catch((error) => console.log('Error:', error)))
        .catch((error) => console.log('Error:', error));
}

function renderTodoList(todos) {
    const todoList = document.getElementById(todoListId);
    while (todoList.firstChild) {
        todoList.removeChild(todoList.lastChild);
    }
    todos.forEach((todo) => renderTodo(todo));
}

function renderTodo(todo) {
    const todoList = document.getElementById(todoListId);
    let li = document.createElement("li");
    li.textContent = `${todo.title} `;
    let deleteButton = document.createElement("button");
    deleteButton.textContent = "Delete";
    deleteButton.onclick = function() {deleteTodo(todo.id)};
    li.appendChild(deleteButton);
    todoList.appendChild(li);
}
```
This code fetches the list of todos from the API when the page loads, and renders them in an unordered list with a delete button for each item. It also allows adding new todos by posting to /api/todos and deleting existing ones by sending a DELETE request to /api/todos/{id}.