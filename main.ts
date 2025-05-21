// main.ts - Console ToDo List (TS)

type Task = {
  task: string;
  completed: boolean;
};

let todoList: Task[] = [];

function addTask(task: string): void {
  todoList.push({ task, completed: false });
  console.log(`Task added: "${task}"`);
}

function completeTask(index: number): void {
  if (todoList[index]) {
    todoList[index].completed = true;
    console.log(`Task completed: "${todoList[index].task}"`);
  } else {
    console.log("Invalid index.");
  }
}

function listTasks(): void {
  console.log("To-Do List:");
  todoList.forEach((item, idx) => {
    console.log(`${idx + 1}. [${item.completed ? "x" : " "}] ${item.task}`);
  });
}

// Sample operations
addTask("Learn TypeScript");
addTask("Create a TypeScript app");
completeTask(1);
listTasks();
