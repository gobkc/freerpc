import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk

from ui.editable_json_tree import EditableJsonTree


class CenterPanel(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self.window = window

        # ===== 顶部：URL + Send 按钮 =====
        top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

        self.url_entry = Gtk.Entry()
        self.url_entry.set_placeholder_text("https://host_addr")
        self.url_entry.set_hexpand(True)

        send_btn = Gtk.Button(label="Send Request")
        send_btn.get_style_context().add_class("important_btn")
        send_btn.connect("clicked", self.on_send_clicked)

        top_bar.append(self.url_entry)
        top_bar.append(send_btn)

        self.append(top_bar)

        # 标题
        self.api_label = self.create_section_label(" Select an API")
        self.append(self.api_label)

        # ===== Paned 开始 =====
        paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        paned.get_style_context().add_class("parameter_paned")
        paned.set_vexpand(True)

        # ---------------- JSON 输入 ----------------
        sample_data = {
            "name": "example",
            "version": 1.0,
            "test": False,
            "active": True,
            "tags": ["gtk", "json", "tree"],
            "metadata": {"author": "user", "count": 42, "nullable": None},
        }
        self.textview = EditableJsonTree(sample_data)
        self.textview.set_theme("dark")
        self.textview.add_css_class("editable_json_tree_dark")

        json_scrolled = Gtk.ScrolledWindow()
        json_scrolled.set_overlay_scrolling(False)
        json_scrolled.set_child(self.textview)
        json_scrolled.set_vexpand(True)

        paned.set_start_child(json_scrolled)

        # ---------------- Meta 区 ----------------
        meta_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        meta_label = self.create_section_label(" Metadata")
        meta_container.append(meta_label)

        meta_data = {
            "library": "GTK4",
            "language": "Python",
            "features": ["collapsible", "editable", "searchable"],
            "nested": {"level2": {"level3": "deep value"}},
        }
        self.meta_textview = EditableJsonTree(meta_data)
        self.meta_textview.set_theme("dark")
        self.meta_textview.add_css_class("editable_json_tree_dark")

        meta_scrolled = Gtk.ScrolledWindow()
        meta_scrolled.set_overlay_scrolling(False)
        meta_scrolled.set_child(self.meta_textview)
        meta_scrolled.set_vexpand(True)

        meta_container.append(meta_scrolled)

        paned.set_end_child(meta_container)

        self.append(paned)
        # ===== Paned 结束 =====

    def set_api(self, api_name):
        self.api_label.set_text(f"API: {api_name}")

    def get_json_text(self):
        buffer = self.textview.get_buffer()
        start, end = buffer.get_bounds()
        return buffer.get_text(start, end, True)

    def set_json_text(self, text):
        buffer = self.textview.get_buffer()
        buffer.set_text(text)

    def on_send_clicked(self, button):
        url = self.url_entry.get_text()
        print(f"Send gRPC request to: {url}")

    def create_section_label(self, text):
        label = Gtk.Label(label=text)

        label.set_xalign(0)
        label.set_yalign(0.5)
        label.set_hexpand(True)

        label.set_margin_top(16)
        label.set_margin_start(16)
        label.set_margin_bottom(6)

        label.add_css_class("section-title")

        return label
