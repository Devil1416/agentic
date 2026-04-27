import os
import json
import argparse
from typing import List, Dict

class TodoList:
    def __init__(self, file_path: str):
        self.file_path = file_path
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump([], f)

    def load_tasks(self) -> List[Dict]:
        with open(self.file_path, 'r') as f:
            return json.load(f)

    def save_tasks(self, tasks: List[Dict]):
        with open(self.file_path, 'w') as f:
            json.dump(tasks, f)

    def add_task(self, task: Dict):
        tasks = self.load_tasks()
        tasks.append(task)
        self.save_tasks(tasks)

    def view_tasks(self):
        return self.load_tasks()

def main():
    parser = argparse.ArgumentParser(description='Manage your tasks')
    subparsers = parser.add_subparsers(dest='command')

    add_parser = subparsers.add_parser('add', help='Add a new task')
    add_parser.add_argument('name', type=str, help='Name of the task')
    add_parser.add_argument('description', type=str, help='Description of the task')

    view_parser = subparsers.add_parser('view', help='View all tasks')

    args = parser.parse_args()

    todo_list = TodoList(file_path='tasks.json')

    if args.command == 'add':
        task = {'name': args.name, 'description': args.description}
        todo_list.add_task(task)
    elif args.command == 'view':
        tasks = todo_list.view_tasks()
        for task in tasks:
            print(f"Name: {task['name']}, Description: {task['description']}")

if __name__ == "__main__":
    main()