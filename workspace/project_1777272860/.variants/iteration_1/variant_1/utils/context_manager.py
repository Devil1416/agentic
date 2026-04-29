import json
import os

def save_context(memory, codebase_context, task_description, output_file):
    context = {
        'memory': memory,
        'codebase_context': codebase_context,
        'task_description': task_description
    }
    
    with open(output_file, 'w') as file:
        json.dump(context, file)
        
def main():
    save_context('sample memory', 'sample codebase context', 'sample task description', 'context_block.json')

if __name__ == "__main__":
    main()