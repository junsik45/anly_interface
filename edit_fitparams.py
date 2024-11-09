import urwid
import json
import sys
import logging

logging.basicConfig(
    filename='app_debug.log',  # Log file name
    filemode='w',               # Append mode
    level=logging.DEBUG,        # Log level
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)

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
        self.current_path = ['fit_ranges']
        self.current_dir = self.get_current_dir()
        self.history = []  # To keep track of navigation history
        self.editing = False  # Flag to indicate if editing is active
        self.adding = False  # Flag to indicate if adding is active
        self.adding_type = None  # Type of item being added ('d' or 'f')

        # Initialize UI components with CircularListBox
        self.listbox = CircularListBox(urwid.SimpleFocusListWalker([]))

        # Create a frame to hold the listbox and a footer
        self.frame = urwid.Frame(
            header=urwid.Text("Directory Explorer - Current Path: /" + "/".join(self.current_path) + " (Press 'q' to quit)"),
            body=self.listbox,
            footer=urwid.Text("Use Arrow Keys to navigate, Enter to enter, 'r' to rename, 'e' to edit data, 'a' to add, 'd' to delete, Backspace to go back.")
        )
        # after frame, then you can update_directory_view
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
        self.frame.header = urwid.Text(f"FitParams Explorer - Current Path: {path} (Press 'q' to quit)")

        # Create a list of selectable items with icons and color coding
        items = []
        for folder in contents:
            if folder == "(Empty)":
                text = folder
                items.append(urwid.AttrMap(urwid.SelectableIcon(text, 0), None, focus_map='reversed'))
            else:
                value = self.current_dir[folder]
                if isinstance(value, dict):
                    if value:
                        # Directory with contents
                        icon = "[D] "
                    else:
                        # Empty Directory
                        icon = "[D] "
                    text = icon + folder
                    attr = 'dir'
                else:
                    # Data node
                    icon = "[F] "
                    text = icon + folder + f" = {value}"
                    attr = 'file'

                items.append(urwid.AttrMap(urwid.SelectableIcon(text, 0), attr, focus_map='reversed'))

        # Update the listbox
        self.listbox.body = urwid.SimpleFocusListWalker(items)
    def keypress(self, key):
        logging.debug("Key pressed: %s"%(key))
        if self.editing:
            logging.debug("Currently editing: %s"%(self.edit_type))
            if self.edit_type == 'add_choice':
                if key == 'enter':
                    choice = self.add_choice_edit.get_edit_text().strip().lower()
                    if choice in ('d', 'f'):
                        self.initiate_add_name(choice)
                    else:
                        self.show_message("Invalid choice. Press 'd' for directory or 'f' for file.")
                    # self.editing = False
                    # self.edit_type = None
                    return  # Prevent further processing
                elif key == 'esc':
                    # Cancel adding
                    self.editing = False
                    self.edit_type = None
                    self.loop.widget = self.frame
                    return  # Prevent further processing
                else:
                    # Let the Edit widget handle other keys
                    self.add_choice_edit.keypress((0,), key)
                    return  # Prevent further processing

            elif self.edit_type == 'add_name':
                logging.debug("Currently editing: %s"%(self.edit_type))
                if key == 'enter':
                    new_name = self.add_edit.get_edit_text().strip()
                    if new_name:
                        self.apply_add_key(new_name, self.adding_type)
                    self.editing = False
                    self.edit_type = None
                    self.loop.widget = self.frame
                    return  # Prevent further processing
                elif key == 'esc':
                    # Cancel adding
                    self.editing = False
                    self.edit_type = None
                    self.loop.widget = self.frame
                    return  # Prevent further processing
                else:
                    # Let the Edit widget handle other keys
                    self.add_edit.keypress((0,), key)
                    return  # Prevent further processing

            elif self.edit_type == 'rename':
                if key == 'enter':
                    new_name = self.edit_edit.get_edit_text().strip()
                    if new_name:
                        self.apply_rename(new_name)
                    self.editing = False
                    self.edit_type = None
                    self.loop.widget = self.frame
                    return  # Prevent further processing
                elif key == 'esc':
                    # Cancel renaming
                    self.editing = False
                    self.edit_type = None
                    self.loop.widget = self.frame
                    return  # Prevent further processing
                else:
                    # Let the Edit widget handle other keys
                    self.edit_edit.keypress((0,), key)
                    return  # Prevent further processing

            elif self.edit_type == 'edit_data':
                if key == 'enter':
                    new_data = self.edit_edit.get_edit_text().strip()
                    if new_data:
                        self.apply_edit_data(new_data)
                    self.editing = False
                    self.edit_type = None
                    self.loop.widget = self.frame
                    return  # Prevent further processing
                elif key == 'esc':
                    # Cancel editing data
                    self.editing = False
                    self.edit_type = None
                    self.loop.widget = self.frame
                    return  # Prevent further processing
                else:
                    # Let the Edit widget handle other keys
                    self.edit_edit.keypress((0,), key)
                    return  # Prevent further processing
            elif self.edit_type == 'add_data':
                if key == 'enter':
                    new_data = self.edit_edit.get_edit_text().strip()
                    if new_data:
                        self.apply_add_data(new_data)
                    self.editing = False
                    self.loop.widget = self.frame
                elif key == 'esc':
                    self.editing = False
                    self.loop.widget = self.frame
                else:
                    self.edit_edit.keypress((0,), key)

            elif self.edit_type == 'delete_confirm':
                if key == 'enter':
                    confirmation = self.delete_confirm_edit.get_edit_text().strip()
                    self.apply_delete_key(confirmation)
                    self.editing = False
                    self.edit_type = None
                    self.loop.widget = self.frame
                    return  # Prevent further processing
                elif key == 'esc':
                    # Cancel deletion
                    self.editing = False
                    self.edit_type = None
                    self.loop.widget = self.frame
                    return  # Prevent further processing
                else:
                    # Let the Edit widget handle other keys
                    self.delete_confirm_edit.keypress((0,), key)
                    return  # Prevent further processing

            elif self.edit_type == 'delete_data_confirm':
                if key == 'enter':
                    confirmation = self.delete_data_confirm_edit.get_edit_text().strip()
                    self.apply_delete_data(confirmation)
                    self.editing = False
                    self.edit_type = None
                    self.loop.widget = self.frame
                    return  # Prevent further processing
                elif key == 'esc':
                    # Cancel data deletion
                    self.editing = False
                    self.edit_type = None
                    self.loop.widget = self.frame
                    return  # Prevent further processing
                else:
                    # Let the Edit widget handle other keys
                    self.delete_data_confirm_edit.keypress((0,), key)
                    return  # Prevent further processing
        else:
            # Handle main navigation keypresses
            if key in ('q', 'Q', 'esc'):
                raise urwid.ExitMainLoop()

            elif key == 'enter':
                logging.debug("Currently main: %s, %r"%(key, self.editing))
                focus_widget, focus_position = self.listbox.get_focus()
                if focus_widget is None:
                    return
                selected = focus_widget.original_widget.get_text()[0]
                if selected.startswith("[D] "):
                    folder = selected[4:]
                    if folder == "(Empty)":
                        return
                    # Enter the selected directory
                    self.history.append(list(self.current_path))
                    self.current_path.append(folder)
                    self.update_directory_view()
                elif selected.startswith("[F] "):
                    # Optionally handle file/data node selection
                    pass

            elif key == 'r':
                # Initiate renaming
                focus_widget, focus_position = self.listbox.get_focus()
                if focus_widget is None:
                    return
                selected = focus_widget.original_widget.get_text()[0]
                if selected.startswith("[D] ") or selected.startswith("[F] "):
                    self.initiate_rename(selected)
                return

            elif key == 'e':
                # Initiate editing data node
                focus_widget, focus_position = self.listbox.get_focus()
                if focus_widget is None:
                    return
                selected = focus_widget.original_widget.get_text()[0]
                if selected.startswith("[F] "):
                    self.initiate_edit_data(selected)
                else:
                    self.show_message("Selected item is not a data node.")
                return

            elif key == 'a':
                # Initiate adding a new key
                self.initiate_add_key()
                return

            elif key == 'd':
                # Initiate deleting a key
                focus_widget, focus_position = self.listbox.get_focus()
                if focus_widget is None:
                    return
                selected = focus_widget.original_widget.get_text()[0]
                if selected.startswith("[D] ") or selected.startswith("[F] "):
                    self.initiate_delete_key(selected)
                return

            elif key == 'backspace':
                if self.history:
                    self.current_path = self.history.pop()
                    self.update_directory_view()
            elif key in ['up','down']:
                # Handle navigation keys (up/down)
                self.listbox.keypress((0,), key)

            else:
                # Unexpected key press
                self.show_message(f"Unexpected key: {key}")
                logging.warning("Unexpected key pressed: %s", key)

    def initiate_delete_key(self, selected):
        # Determine if the selected item is a directory or data node
        if selected.startswith("[D] "):
            item_type = 'directory'
            current_name = selected[4:]
        elif selected.startswith("[F] "):
            item_type = 'file'
            current_name = selected[4:].split('=')[0].strip()
        else:
            item_type = 'unknown'
            current_name = selected

        if item_type == 'unknown':
            self.show_message("Selected item cannot be deleted.")
            return

        # Create a confirmation prompt
        confirm_text = f"Are you sure you want to delete '{current_name}' ({item_type})? (y/n)"
        self.delete_confirm_edit = urwid.Edit(confirm_text)
        fill = urwid.Filler(self.delete_confirm_edit, valign='top')
        overlay = urwid.Overlay(
            urwid.LineBox(fill),
            self.frame,
            align='center',
            width=('relative', 60),
            valign='middle',
            height=4
        )
        self.loop.widget = overlay
        self.editing = True
        self.edit_type = 'delete_confirm'
        self.delete_item_type = item_type
        self.delete_item_name = current_name

    def apply_delete_key(self, confirmation):
        if confirmation.lower() == 'y':
            # Perform deletion
            if self.delete_item_type == 'directory':
                # Ensure the directory is empty
                if isinstance(self.current_dir[self.delete_item_name], dict) and self.current_dir[self.delete_item_name]:
                    self.show_message(f"Error: Directory '{self.delete_item_name}' is not empty.")
                    return
                else:
                    del self.current_dir[self.delete_item_name]
            elif self.delete_item_type == 'file':
                del self.current_dir[self.delete_item_name]
            else:
                self.show_message("Error: Unknown item type.")
                return

            # Save changes to JSON (optional)
            save_directory_tree(self.json_file, self.directory_tree)

            # Refresh the UI
            self.update_directory_view()
            self.show_message(f"Deleted '{self.delete_item_name}' successfully.")
        else:
            # Cancel deletion
            self.show_message("Deletion cancelled.")
    def initiate_add_data(self, selected):
        # Ensure the selected item is a data node
        if selected.startswith("[F] "):
            parts = selected[4:].split('=')
            if len(parts) != 2:
                self.show_message("Invalid data node format.")
                return
            current_name = parts[0].strip()
            current_data = parts[1].strip()
        else:
            self.show_message("Selected item is not a data node.")
            return

        # Create an Edit widget for adding data
        self.edit_edit = urwid.Edit(('reversed', f"Set data for '{current_name}': "), edit_text=current_data)
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
        self.edit_type = 'add_data'

        # Store the item being edited
        self.item_to_edit = current_name

    def apply_add_data(self, new_data):
        # Attempt to convert new_data to int, float, or keep as string
        try:
            if '.' in new_data:
                converted_data = float(new_data)
            else:
                converted_data = int(new_data)
        except ValueError:
            # Keep as string if not a number
            converted_data = new_data

        # Update the data node in the directory tree
        self.current_dir[self.item_to_edit] = converted_data

        # Save changes to JSON (optional)
        save_directory_tree(self.json_file, self.directory_tree)

        # Refresh the UI
        self.update_directory_view()
    def initiate_delete_data(self, selected):
        # Ensure the selected item is a data node
        if selected.startswith("[F] "):
            parts = selected[4:].split('=')
            if len(parts) != 2:
                self.show_message("Invalid data node format.")
                return
            current_name = parts[0].strip()
            current_data = parts[1].strip()
        else:
            self.show_message("Selected item is not a data node.")
            return

        # Create a confirmation prompt
        confirm_text = f"Are you sure you want to delete data for '{current_name}'? (y/n)"
        self.delete_data_confirm_edit = urwid.Edit(confirm_text)
        fill = urwid.Filler(self.delete_data_confirm_edit, valign='top')
        overlay = urwid.Overlay(
            urwid.LineBox(fill),
            self.frame,
            align='center',
            width=('relative', 60),
            valign='middle',
            height=4
        )
        self.loop.widget = overlay
        self.editing = True
        self.edit_type = 'delete_data_confirm'
        self.delete_data_item_name = current_name

    def apply_delete_data(self, confirmation):
        if confirmation.lower() == 'y':
            # Delete data (set to None or another default)
            self.current_dir[self.delete_data_item_name] = None  # Or use del self.current_dir[self.delete_data_item_name]

            # Save changes to JSON (optional)
            save_directory_tree(self.json_file, self.directory_tree)

            # Refresh the UI
            self.update_directory_view()
            self.show_message(f"Deleted data for '{self.delete_data_item_name}' successfully.")
        else:
            # Cancel deletion
            self.show_message("Data deletion cancelled.")

    def initiate_rename(self, selected):
        # Extract the current name without the icon
        if selected.startswith("[D] "):
            current_name = selected[4:]
        elif selected.startswith("[F] "):
            current_name = selected[4:].split('=')[0].strip()
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
        self.edit_type = 'rename'

        # Store the item being renamed
        self.item_to_rename = current_name
    def initiate_add_key(self):
        # Prompt user to choose between directory or data node
        logging.debug("Initiate Add Key called")
        question = urwid.Text("Add (d)irectory or (f)ile? ")
        self.add_choice_edit = urwid.Edit()
        pile = urwid.Pile([question, self.add_choice_edit])
        fill = urwid.Filler(pile, valign='top')
        overlay = urwid.Overlay(
            urwid.LineBox(fill),
            self.frame,
            align='center',
            width=('relative', 50),
            valign='middle',
            height=4
        )
        self.loop.widget = overlay
        self.editing = True
        self.edit_type = 'add_choice'
        logging.debug("Set edit_type to %s"%(self.edit_type))
    def initiate_add_name(self, choice):
        # Prompt for the new key name based on choice
        logging.debug("Initiate Add Name called with choice: %s"%(choice))
        if choice == 'd':
            prompt = "Enter the name of the new directory: "
        elif choice == 'f':
            prompt = "Enter the name of the new data node: "
        else:
            prompt = "Enter the new name: "  # Fallback

        self.add_edit = urwid.Edit(('reversed', prompt))        
        fill = urwid.Filler(self.add_edit, valign='top')
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
        self.edit_type = 'add_name'
        self.adding_type = choice  # Store the type ('d' or 'f')
        logging.debug("Set edit_type to %s and adding_type to %s"%(self.edit_type, self.adding_type))
        logging.debug("Overlay set; editing should still be True: %s" % self.editing)


    def apply_add_key(self, new_name, item_type):
        # Validate the new name
        logging.debug("Apply Add Key called with name: %s, type: %s"%(new_name, item_type))
        if new_name in self.current_dir:
            self.show_message(f"Error: '{new_name}' already exists.")
            return

        if item_type == 'd':
            # Add a new directory
            self.current_dir[new_name] = {}
        elif item_type == 'f':
            # Add a new data node with a default value (e.g., 0)
            self.current_dir[new_name] = 0  # Customize default value as needed
        else:
            self.show_message("Error: Unknown item type.")
            return

        # Save changes to JSON (optional)
        save_directory_tree(self.json_file, self.directory_tree)

        # Refresh the UI
        self.update_directory_view()
        self.show_message(f"Added '{new_name}' successfully.")

        # Reset state variables
        self.editing = False
        self.edit_type = None
        self.adding_type = None

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

    def initiate_edit_data(self, selected):
        # Extract the current name and data
        if selected.startswith("[F] "):
            parts = selected[4:].split('=')
            if len(parts) != 2:
                self.show_message("Invalid data node format.")
                return
            current_name = parts[0].strip()
            current_data = parts[1].strip()
        else:
            self.show_message("Selected item is not a data node.")
            return

        # Create an Edit widget for editing data
        self.edit_edit = urwid.Edit(('reversed', f"Editing '{current_name}' data: "), edit_text=current_data)
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
        self.edit_type = 'edit_data'

        # Store the item being edited
        self.item_to_edit = current_name

    def apply_edit_data(self, new_data):
        # Attempt to convert new_data to int, float, or keep as string
        try:
            if '.' in new_data:
                converted_data = float(new_data)
            else:
                converted_data = int(new_data)
        except ValueError:
            # Keep as string if not a number
            converted_data = new_data

        # Update the data node in the directory tree
        self.current_dir[self.item_to_edit] = converted_data

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
            ('dir', 'dark green', ''),
            ('file', 'dark cyan', ''),
            ('reversed', 'standout', ''),
        ]
        self.loop = urwid.MainLoop(self.frame, palette, unhandled_input=self.keypress)
        self.loop.run()

def main():
    directory_tree = load_directory_tree('a09m135.json')
    explorer = DirectoryExplorer(directory_tree, 'a09m135.json')
    explorer.run()

if __name__ == "__main__":
    main()

