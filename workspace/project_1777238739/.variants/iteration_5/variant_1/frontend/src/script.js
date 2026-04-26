// frontend/src/script.js

document.addEventListener('DOMContentLoaded', () => {
    // Fetch tasks from the API and render them
    fetch('/api/tasks')
        .then(response => response.json())
        .then(data => data.forEach(task => renderTask(task)))
        .catch(error => console.log('Error:', error));
});

// Render a single task element
function renderTask(task) {
    const list = document.getElementById('tasks');
    const li = document.createElement('li');
    li.dataset.id = task.id;
    
    if (task.completed) {
        li.classList.add('completed');
    }
    
    li.innerHTML = `<input type="checkbox" ${task.completed ? 'checked' : ''}> ${task.content} <button class="delete">Delete</button>`;
    
    // Handle checkbox change
    const checkbox = li.querySelector('input');
    checkbox.addEventListener('change', () => {
        fetch(`/api/tasks/${task.id}/toggle_completed`, {method: 'PUT'})
            .then(() => location.reload())
            .catch(error => console.log('Error:', error));
    });
    
    // Handle delete button click
    const deleteButton = li.querySelector('.delete');
    deleteButton.addEventListener('click', () => {
        fetch(`/api/tasks/${task.id}`, {method: 'DELETE'})
            .then(() => location.reload())
            .catch(error => console.log('Error:', error));
    });
    
    list.appendChild(li);
}

// Handle form submission to add a new task
document.getElementById('new-task').addEventListener('submit', event => {
    event.preventDefault();
    const content = document.getElementById('content').value;
    fetch('/api/tasks', {method: 'POST', body: JSON.stringify({content}), headers: {'Content-Type': 'application/json'}})
        .then(() => location.reload())
        .catch(error => console.log('Error:', error));
});