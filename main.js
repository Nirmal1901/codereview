// main.js - Console ToDo List (JS)

let todoList = [];

function addTask(task) {
  todoList.push({ task, completed: false });
  console.log(`Task added: "${task}"`);
}

function completeTask(index) {
  if (todoList[index]) {
    todoList[index].completed = true;
    console.log(`Task completed: "${todoList[index].task}"`);
  } else {
    console.log("Invalid index.");
  }
}

function listTasks() {
  console.log("To-Do List:");
  todoList.forEach((item, idx) => {
    console.log(`${idx + 1}. [${item.completed ? "x" : " "}] ${item.task}`);
  });
}

// Sample operations
addTask("Learn JavaScript");
addTask("Build a project");
completeTask(0);
listTasks();
