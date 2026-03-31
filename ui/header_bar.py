import gi

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

        # 添加 proto 按钮
        btn_add_proto = Gtk.Button(label="Add Proto")
        btn_add_proto.connect("clicked", self.handler.on_add_proto)
        self.append(btn_add_proto)

        # 格式化 JSON 按钮
        btn_format = Gtk.Button(label="Format JSON")
        btn_format.connect("clicked", self.handler.on_format_json)
        self.append(btn_format)
