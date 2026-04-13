import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk

from ui.json_gutter_renderer import JsonGutterRenderer


class RightPanel(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        self.window = window
        self.set_margin_top(0)
        self.set_margin_bottom(0)
        self.set_margin_start(0)
        self.set_margin_end(0)

        notebook = Gtk.Notebook()
        self.append(notebook)
        notebook.set_vexpand(True)
        notebook.set_hexpand(True)

        # 响应
        self.response_view = JsonGutterRenderer(theme="dark", show_line_numbers=False)
        self.response_view.get_style_context().add_class("json_gutter")
        self.response_view.textview.set_editable(False)
        self.response_view.textview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.response_view.textview.set_cursor_visible(False)

        scrolled1 = Gtk.ScrolledWindow()
        scrolled1.set_child(self.response_view)

        notebook.append_page(scrolled1, Gtk.Label(label="Response"))

        # 过程日志
        self.log_view = JsonGutterRenderer(theme="dark", show_line_numbers=False)
        self.response_view.get_style_context().add_class("json_gutter")
        self.log_view.textview.set_editable(False)
        self.log_view.textview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.log_view.textview.set_cursor_visible(False)

        scrolled2 = Gtk.ScrolledWindow()
        scrolled2.set_child(self.log_view)

        notebook.append_page(scrolled2, Gtk.Label(label="Execution Log"))
