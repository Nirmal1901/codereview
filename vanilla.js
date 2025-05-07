// toDoList.js - Simple To-Do App in Vanilla JS

// Select DOM elements
const taskInput = document.getElementById('task-input');
const addButton = document.getElementById('add-btn');
const taskList = document.getElementById('task-list');

// Initialize task array
let tasks = [];

// Load tasks from local storage
function loadTasks() {
  const storedTasks = localStorage.getItem('tasks');
  if (storedTasks) {
    tasks = JSON.parse(storedTasks);
  }
}

// Save tasks to local storage
function saveTasks() {
  localStorage.setItem('tasks', JSON.stringify(tasks));
}

// Render tasks in the UI
function renderTasks() {
  taskList.innerHTML = '';
  tasks.forEach((task, index) => {
    const li = document.createElement('li');
    li.className = 'task-item';

    const span = document.createElement('span');
    span.textContent = task.text;
    span.style.textDecoration = task.completed ? 'line-through' : 'none';

    const completeBtn = document.createElement('button');
    completeBtn.textContent = task.completed ? 'Undo' : 'Complete';
    completeBtn.className = 'complete-btn';
    completeBtn.onclick = () => toggleTask(index);

    const deleteBtn = document.createElement('button');
    deleteBtn.textContent = 'Delete';
    deleteBtn.className = 'delete-btn';
    deleteBtn.onclick = () => deleteTask(index);

    li.appendChild(span);
    li.appendChild(completeBtn);
    li.appendChild(deleteBtn);
    taskList.appendChild(li);
  });
}

// Add a new task
function addTask() {
  const text = taskInput.value.trim();
  if (text === '') {
    alert('Please enter a task.');
    return;
  }
  const task = { text, completed: false };
  tasks.push(task);
  taskInput.value = '';
  saveTasks();
  renderTasks();
}

// Toggle task completion
function toggleTask(index) {
  tasks[index].completed = !tasks[index].completed;
  saveTasks();
  renderTasks();
}

// Delete a task
function deleteTask(index) {
  tasks.splice(index, 1);
  saveTasks();
  renderTasks();
}

// Add event listeners
addButton.addEventListener('click', addTask);
taskInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    addTask();
  }
});

// Initial load
loadTasks();
renderTasks();

// Styling (You can move this to a CSS file)
const style = document.createElement('style');
style.textContent = `
  #task-list {
    list-style: none;
    padding: 0;
  }
  .task-item {
    margin: 8px 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .task-item button {
    margin-left: 8px;
    padding: 5px 10px;
  }
`;
document.head.appendChild(style);

// Optional: Clear all tasks (button not shown in HTML)
function clearTasks() {
  if (confirm('Are you sure you want to delete all tasks?')) {
    tasks = [];
    saveTasks();
    renderTasks();
  }
}

// You can call clearTasks() from browser console if needed
// e.g., clearTasks();
