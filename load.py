import json

def load_directory_tree(json_file):
    with open(json_file, 'r') as f:
        return json.load(f)

