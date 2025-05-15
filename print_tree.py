# print_tree.py
import os

def print_tree(root: str, prefix: str = ""):
    entries = sorted(os.listdir(root))
    for idx, name in enumerate(entries):
        path = os.path.join(root, name)
        connector = "└── " if idx == len(entries) - 1 else "├── "
        print(prefix + connector + name)
        if os.path.isdir(path):
            extension = "    " if idx == len(entries) - 1 else "│   "
            print_tree(path, prefix + extension)

if __name__ == "__main__":
    print_tree(".")
