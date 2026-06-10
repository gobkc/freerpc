import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from handlers.left_panel_handler import LeftPanelHandler
from ui.json_tree import JsonTree


class LeftPanel(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        self.context = window.context
        self.window = window
        self.handler = LeftPanelHandler(self)

        # =========================
        # Header
        # =========================
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        label = Gtk.Label(label="Proto & APIs")
        label.set_xalign(0)
        label.set_hexpand(True)

        settings_btn = Gtk.Button(label="⚙")
        settings_btn.add_css_class("settings")
        settings_btn.set_tooltip_text("settings")
        settings_btn.connect("clicked", self.handler.show_settings_form)

        header_box.append(label)
        header_box.append(settings_btn)

        self.append(header_box)

        # =========================
        # Tree
        # =========================
        self.tree = JsonTree(editable=False, depth=2)
        self.tree.set_vexpand(True)
        self.tree.set_hexpand(False)
        self.tree.connect("node-activated", self.handler.on_api_selected)

        self.append(self.tree)

        self.handler.on_left_tree_init()
