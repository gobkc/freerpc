import gi

from ui.buttons import make_icon_text_button

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk

from handlers.toolbar_handler import ToolbarHandler


class HeaderBar(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        self.window = window
        self.handler = ToolbarHandler(window)

        self.set_margin_top(6)
        self.set_margin_bottom(6)
        self.set_margin_start(6)
        self.set_margin_end(6)

        btn_add_proto = make_icon_text_button(
            "📄", "", self.handler.on_add_proto, "icon_btn"
        )
        self.append(btn_add_proto)

        btn_format = make_icon_text_button(
            "{}", "", self.handler.on_format_json, "icon_btn"
        )
        self.append(btn_format)
