import urwid
import json

import urwid

class CircularListBox(urwid.ListBox):
    def keypress(self, size, key):
        if key == 'up':
            focus_widget, focus_position = self.body.get_focus()
            if focus_position == 0:
                # Move focus to the last item
                self.body.set_focus(len(self.body) - 1)
                return
        elif key == 'down':
            focus_widget, focus_position = self.body.get_focus()
            if focus_position == len(self.body) - 1:
                # Move focus to the first item
                self.body.set_focus(0)
                return
        # For other keys or non-edge cases, use the default behavior
        return super().keypress(size, key)


class DirectoryExplorer:
    def __init__(self, directory_tree):
        self.directory_tree = directory_tree
        self.current_path = ['root']
        self.current_dir = self.get_current_dir()
        self.history = []  # To keep track of navigation history

        # Initialize UI components
        self.listbox = CircularListBox(urwid.SimpleFocusListWalker([]))
        self.update_directory_view()


        # Create a frame to hold the listbox and a footer
        self.frame = urwid.Frame(
            header=urwid.Text("Directory Explorer (Press 'q' to quit)"),
            body=self.listbox,
            footer=urwid.Text("Use Arrow Keys to navigate, Enter to enter a directory, Backspace to go back.")
        )

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

        # Create a list of selectable items
        items = [urwid.Text(folder) for folder in contents]
        selectable_items = [urwid.AttrMap(urwid.SelectableIcon(folder, 0), None, focus_map='reversed') for folder in contents]

        self.listbox.body = urwid.SimpleFocusListWalker(selectable_items)

    def keypress(self, key):
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()

        elif key == 'enter':
            focus_widget, idx = self.listbox.get_focus()
            selected = focus_widget.original_widget.get_text()[0]
            if selected == "(Empty)":
                return
            # Enter the selected directory
            self.history.append(list(self.current_path))
            self.current_path.append(selected)
            self.update_directory_view()

        elif key == 'up':
            self.listbox.keypress((0,), 'up')

        elif key == 'down':
            self.listbox.keypress((0,), 'down')

        elif key == 'backspace':
            if self.history:
                self.current_path = self.history.pop()
                self.update_directory_view()

    def run(self):
        palette = [
            ('reversed', 'standout', ''),
        ]
        loop = urwid.MainLoop(self.frame, palette, unhandled_input=self.keypress)
        loop.run()

