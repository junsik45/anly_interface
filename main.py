from explorer import *
from load import *

def main():
    directory_tree = load_directory_tree('dir.tree.json')
    explorer = DirectoryExplorer(directory_tree)
    explorer.run()

if __name__ == "__main__":
    main()

