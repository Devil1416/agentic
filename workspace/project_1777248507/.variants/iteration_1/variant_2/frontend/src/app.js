Based on the provided project plan and rules, here is a raw source code for frontend/src/app.js that meets all requirements:

```javascript
// frontend/src/app.js
const apiBase = "http://localhost:5000";
const todoListId = ""; // Add the id of the HTML element where you want to display the list

window.onload = function() {
    fetch(apiBase + "/api/todos")
        .then(response => response.json())
        .then(data => renderTodoList(data, todoListId));
};

function addTodoItem(title) {
    const data = JSON.stringify({ title: title });
    
    fetch(apiBase + "/api/todos", {
        method: "POST",
        headers: {
            'Content-Type': 'application/json'
        },
        body: data
    })
    .then(() => fetch(apiBase + "/api/todos")
                .then(response => response.json())
                .then(data => renderTodoList(data, todoListId)));
}

function deleteTodoItem(id) {
    fetch(`${apiBase}/api/todos/${id}`, { method: "DELETE" })
        .then(() => fetch(apiBase + "/api/todos")
                    .then(response => response.json())
                    .then(data => renderTodoList(data, todoListId)));
}

function renderTodoList(todos, listId) {
    const listElement = document.getElementById(listId);
    
    // Clear the existing content of the list element
    while (listElement.firstChild) {
        listElement.removeChild(listElement.firstChild);
    }

    todos.forEach((todo) => {
        const todoItem = document.createElement("div");
        
        // Create a checkbox for marking the item as done
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.checked = todo.done;
        checkbox.onchange = () => {
            fetch(`${apiBase}/api/todos/${todo.id}`, {
                method: "PUT",
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ done: checkbox.checked })
            });
        };
        
        // Create a button for deleting the item
        const deleteButton = document.createElement("button");
        deleteButton.textContent = "Delete";
        deleteButton.onclick = () => { deleteTodoItem(todo.id); };
        
        todoItem.appendChild(checkbox);
        todoItem.appendChild(document.createTextNode(todo.title));
        todoItem.appendChild(deleteButton);
        listElement.appendChild(todoItem);
    });
}
```

This code assumes that the server is running on localhost at port 5000 and that the Todo items are represented as objects with properties 'id', 'title' and 'done'. It fetches the todo list from the API when the window loads, renders it in a HTML element with id `todoListId`, and handles adding new todos by making a POST request to '/api/todos' and deleting existing ones by making a DELETE request to '/api/todos/{id}'. It also allows marking Todo items as done by changing the 'done' property of the corresponding item on the server.