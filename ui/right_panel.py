import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk


class RightPanel(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        self.window = window
        self.set_margin_top(6)
        self.set_margin_bottom(6)
        self.set_margin_start(6)
        self.set_margin_end(6)

        notebook = Gtk.Notebook()
        self.append(notebook)
        notebook.set_vexpand(True)
        notebook.set_hexpand(True)

        # 响应
        self.response_view = Gtk.TextView()
        self.response_view.set_editable(False)

        scrolled1 = Gtk.ScrolledWindow()
        scrolled1.set_child(self.response_view)

        notebook.append_page(scrolled1, Gtk.Label(label="Response"))

        # 过程日志
        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)

        scrolled2 = Gtk.ScrolledWindow()
        scrolled2.set_child(self.log_view)

        notebook.append_page(scrolled2, Gtk.Label(label="Execution Log"))
