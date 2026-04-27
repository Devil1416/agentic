// frontend/src/script.js

document.addEventListener('DOMContentLoaded', () => {
    const todoList = document.getElementById('todo-list');
    const addTodoForm = document.getElementById('add-todo-form');
    
    // Fetch the list of todos from the server
    fetch('/api/todos')
        .then(response => response.json())
        .then(data => {
            data.forEach((item) => renderTodoItem(item));
        });
    
    addTodoForm.addEventListener('submit', (event) => {
        event.preventDefault();
        
        const content = document.getElementById('new-todo').value;
        fetch('/api/todos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({content})
        })
        .then(response => response.json())
        .then(({id, content}) => renderTodoItem({id, content}))
        .catch(error => console.log('Error:', error));
    });
    
    function renderTodoItem({id, content}) {
        const todoItem = document.createElement('div');
        todoItem.className = 'todo-item';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.addEventListener('change', () => updateTodoStatus(id, checkbox.checked));
        
        const label = document.createElement('label');
        label.textContent = content;
        
        const deleteButton = document.createElement('button');
        deleteButton.textContent = 'Delete';
        deleteButton.addEventListener('click', () => deleteTodo(id));
        
        todoItem.appendChild(checkbox);
        todoItem.appendChild(label);
        todoItem.appendChild(deleteButton);
        
        todoList.appendChild(todoItem);
    }
    
    function updateTodoStatus(id, status) {
        fetch(`/api/todos/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({completed: status})
        })
        .catch(error => console.log('Error:', error));
    }
    
    function deleteTodo(id) {
        fetch(`/api/todos/${id}`, {method: 'DELETE'})
            .then(() => document.getElementById(id).remove())
            .catch(error => console.log('Error:', error));
    }
});