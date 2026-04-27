import json
import argparse
from typing import List, Dict

class TodoList:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.tasks = []
    
    def load(self) -> None:
        try:
            with open(self.file_path, 'r') as f:
                self.tasks = json.load(f)
        except FileNotFoundError:
            pass  # If the file doesn't exist yet, we just start with an empty list of tasks
    
    def save(self) -> None:
        with open(self.file_path, 'w') as f:
            json.dump(self.tasks, f)
    
    def add_task(self, task: str) -> None:
        self.tasks.append({'description': task, 'completed': False})
        self.save()
    
    def view_tasks(self) -> List[Dict[str, str]]:
        return self.tasks

def main():
    parser = argparse.ArgumentParser(description='Manage tasks using a persistent storage mechanism (e.g., JSON file).')
    subparsers = parser.add_subparsers()
    
    add_parser = subparsers.add_parser('add', help='Add a new task to the todo list.')
    add_parser.add_argument('task', type=str, help='The description of the task to be added.')
    add_parser.set_defaults(func=lambda args: todo_list.add_task(args.task))
    
    view_parser = subparsers.add_parser('view', help='View all tasks in the todo list.')
    view_parser.set_defaults(func=lambda _: print(json.dumps(todo_list.view_tasks(), indent=2)))
    
    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    todo_list = TodoList('tasks.json')
    todo_list.load()
    main()