import urwid
import json

def load_directory_tree(json_file):
    with open(json_file, 'r') as f:
        return json.load(f)

def save_directory_tree(json_file, directory_tree):
    with open(json_file, 'w') as f:
        json.dump(directory_tree, f, indent=4)

class CircularListBox(urwid.ListBox):
    def keypress(self, size, key):
        if key == 'up':
            focus_widget, focus_position = self.body.get_focus()
            if focus_position == 0 and len(self.body) > 0:
                # Move focus to the last item
                self.body.set_focus(len(self.body) - 1)
                return
        elif key == 'down':
            focus_widget, focus_position = self.body.get_focus()
            if focus_position == len(self.body) - 1 and len(self.body) > 0:
                # Move focus to the first item
                self.body.set_focus(0)
                return
        # For other keys or non-edge cases, use the default behavior
        return super().keypress(size, key)

class DirectoryExplorer:
    def __init__(self, directory_tree, json_file):
        self.directory_tree = directory_tree
        self.json_file = json_file  # To save changes
        self.current_path = ['root']
        self.current_dir = self.get_current_dir()
        self.history = []  # To keep track of navigation history
        self.editing = False  # Flag to indicate if editing is active

        # Initialize UI components with CircularListBox
        self.listbox = CircularListBox(urwid.SimpleFocusListWalker([]))

        # Create a frame to hold the listbox and a footer
        self.frame = urwid.Frame(
            header=urwid.Text("Directory Explorer - Current Path: /" + "/".join(self.current_path) + " (Press 'q' to quit)"),
            body=self.listbox,
            footer=urwid.Text("Use Arrow Keys to navigate, Enter to enter a directory, 'r' to rename, Backspace to go back.")
        )

        self.update_directory_view()

    def get_current_dir(self):
        dir_ref = self.directory_tree
        for folder in self.current_path:
            dir_ref = dir_ref.get(folder, {})
        return dir_ref

    def update_directory_view(self):
        self.current_dir = self.get_current_dir()
        contents = list(self.current_dir.keys())
        if not contents:
            contents = ["(Empty)"]

        # Update header with current path
        path = "/" + "/".join(self.current_path)
        self.frame.header = urwid.Text(f"Directory Explorer - Current Path: {path} (Press 'q' to quit)")

        # Create a list of selectable items with icons
        items = []
        for folder in contents:
            if isinstance(self.current_dir[folder], dict) and self.current_dir[folder]:
                # Directory with contents
                icon = "[D] "
                text = icon + folder
            elif isinstance(self.current_dir[folder], dict):
                # Empty Directory
                icon = "[D] "
                text = icon + folder
            else:
                # File
                icon = "[F] "
                text = icon + folder
            items.append(urwid.AttrMap(urwid.SelectableIcon(text, 0), None, focus_map='reversed'))

        # Update the listbox
        self.listbox.body = urwid.SimpleFocusListWalker(items)

    def keypress(self, key):
        if self.editing:
            # Currently in editing mode
            if key == 'enter':
                # Submit the new name
                new_name = self.edit_edit.get_edit_text().strip()
                if new_name:
                    self.apply_rename(new_name)
                self.editing = False
                self.loop.widget = self.frame
            elif key == 'esc':
                # Cancel editing
                self.editing = False
                self.loop.widget = self.frame
            else:
                # Let the Edit widget handle other keys
                self.edit_edit.keypress((0,), key)
        else:
            if key in ('q', 'Q'):
                raise urwid.ExitMainLoop()

            elif key == 'enter':
                focus_widget, focus_position = self.listbox.get_focus()
                if focus_widget is None:
                    return
                selected = focus_widget.original_widget.get_text()[0]
                if selected.startswith("[F] "):
                    # Handle file selection
                    file_name = selected[4:]
                    self.show_message(f"Selected file: {file_name}")
                    return
                elif selected.startswith("[D] "):
                    folder = selected[4:]
                    if folder == "(Empty)":
                        return
                    # Enter the selected directory
                    self.history.append(list(self.current_path))
                    self.current_path.append(folder)
                    self.update_directory_view()

            elif key == 'r':
                # Initiate renaming
                focus_widget, focus_position = self.listbox.get_focus()
                if focus_widget is None:
                    return
                selected = focus_widget.original_widget.get_text()[0]
                if selected.startswith("[D] ") or selected.startswith("[F] "):
                    self.initiate_rename(selected)
                return

            elif key == 'backspace':
                if self.history:
                    self.current_path = self.history.pop()
                    self.update_directory_view()

            else:
                # Handle navigation keys (up/down) via ListBox
                self.listbox.keypress((0,), key)

    def initiate_rename(self, selected):
        # Extract the current name without the icon
        if selected.startswith("[D] "):
            current_name = selected[4:]
        elif selected.startswith("[F] "):
            current_name = selected[4:]
        else:
            current_name = selected

        # Create an Edit widget for renaming
        self.edit_edit = urwid.Edit(('reversed', f"Renaming '{current_name}' to: "))
        fill = urwid.Filler(self.edit_edit, valign='top')
        overlay = urwid.Overlay(
            urwid.LineBox(fill),
            self.frame,
            align='center',
            width=('relative', 50),
            valign='middle',
            height=3
        )
        self.loop.widget = overlay
        self.editing = True

        # Store the item being renamed
        self.item_to_rename = current_name

    def apply_rename(self, new_name):
        # Validate new_name (e.g., no duplicates)
        if new_name in self.current_dir:
            self.show_message(f"Error: '{new_name}' already exists.")
            return

        # Rename in the directory tree
        self.current_dir[new_name] = self.current_dir.pop(self.item_to_rename)

        # Save changes to JSON (optional)
        save_directory_tree(self.json_file, self.directory_tree)

        # Update the view
        self.update_directory_view()

    def show_message(self, message):
        # Display a popup message
        text = urwid.Text(message)
        fill = urwid.Filler(text)
        overlay = urwid.Overlay(
            urwid.LineBox(fill),
            self.frame,
            align='center',
            width=('relative', 50),
            valign='middle',
            height=3
        )
        self.loop.widget = overlay

        # Restore the main frame after user input
        def dismiss(key):
            if key in ('enter', 'esc'):
                self.loop.widget = self.frame
                self.loop.unhandled_input = self.keypress  # Restore keypress handler

        self.loop.unhandled_input = dismiss

    def run(self):
        palette = [
            ('reversed', 'standout', ''),
        ]
        self.loop = urwid.MainLoop(self.frame, palette, unhandled_input=self.keypress)
        self.loop.run()

def main():
    directory_tree = load_directory_tree('directory_tree.json')
    explorer = DirectoryExplorer(directory_tree, 'directory_tree.json')
    explorer.run()

if __name__ == "__main__":
    main()

