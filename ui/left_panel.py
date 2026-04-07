import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gio, Gtk

from ui.json_tree import JsonTree


class LeftPanel(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.window = window
        self.set_margin_top(0)
        self.set_margin_bottom(0)
        self.set_margin_start(0)
        self.set_margin_end(0)

        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        label = Gtk.Label(label="Proto & APIs")
        label.set_xalign(0)
        label.set_hexpand(True)
        header_box.append(label)

        settings_btn = Gtk.Button(label="⚙")
        settings_btn.add_css_class("settings")
        settings_btn.set_tooltip_text("settings")
        header_box.append(settings_btn)

        self.append(header_box)

        self.tree = JsonTree(editable=False)
        self.tree.set_vexpand(True)
        self.tree.connect("node-activated", self._on_api_selected)
        self.append(self.tree)

        self.load_demo_apis()

    def load_demo_apis(self):
        data = {
            "UserService": {
                "GetUser": {"request": {"id": 1}, "description": "Get user by ID"},
                "CreateUser": {
                    "request": {"name": "Alice", "email": "alice@example.com"}
                },
            },
            "OrderService": {
                "CreateOrder": {"request": {"userId": 1, "items": ["item1"]}}
            },
        }
        self.tree.set_data(data)

    def _on_api_selected(self, tree, node):
        api_info = node.get_python_value()
        if isinstance(api_info, dict):
            request_template = api_info.get("request", {})
            self.window.center_panel.set_api(node.key, request_template)
