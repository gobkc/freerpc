from utils.json_utils import format_json


class ToolbarHandler:
    def __init__(self, window):
        self.window = window

    def on_add_proto(self, button):
        print("Add proto clicked (TODO)")

    def on_format_json(self, button):
        text = self.window.center_panel.get_json_text()
        formatted = format_json(text)
        self.window.center_panel.set_json_text(formatted)
