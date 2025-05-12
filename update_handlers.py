import os
import re

def update_file(file_path):
    print(f"Processing {file_path}")
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Remove async from function definitions
    content = re.sub(r'async\s+def\s+([a-zA-Z0-9_]+)', r'def \1', content)
    
    # Remove await keywords
    content = re.sub(r'await\s+', '', content)
    
    with open(file_path, 'w') as file:
        file.write(content)
    
    print(f"Updated {file_path}")

def process_directory(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                update_file(file_path)

if __name__ == "__main__":
    process_directory('handlers')