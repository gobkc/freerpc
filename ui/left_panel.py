import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk

from handlers.api_handler import ApiHandler


class LeftPanel(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        self.window = window
        self.handler = ApiHandler(window)

        self.set_margin_top(6)
        self.set_margin_bottom(6)
        self.set_margin_start(6)
        self.set_margin_end(6)

        label = Gtk.Label(label="Proto & APIs")
        self.append(label)

        # API 列表
        self.listbox = Gtk.ListBox()
        self.listbox.connect("row-activated", self.handler.on_api_selected)

        self.append(self.listbox)

        # 示例数据（后续由 proto 解析填充）
        self.add_api("UserService/GetUser")
        self.add_api("OrderService/CreateOrder")

    def add_api(self, name):
        row = Gtk.ListBoxRow()
        label = Gtk.Label(label=name, xalign=0)
        row.set_child(label)
        self.listbox.append(row)
