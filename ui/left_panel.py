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
        settings_btn.connect("clicked", self.show_settings_form)
        header_box.append(settings_btn)

        self.append(header_box)

        self.tree = JsonTree(editable=False)
        self.tree.set_vexpand(True)
        self.tree.connect("node-activated", self._on_api_selected)
        self.append(self.tree)

        self.load_demo_apis()

    def show_settings_form(self, btn):
        self.settings_window = Gtk.Dialog(title="Settings", transient_for=self.window)
        self.settings_window.set_default_size(500, 400)
        self.settings_window.set_modal(True)
        self.settings_window.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.settings_window.add_button("OK", Gtk.ResponseType.OK)
        self.settings_window.get_style_context().add_class("settings_window")

        content = self.settings_window.get_content_area()

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.set_margin_top(12)
        main_box.set_margin_bottom(12)
        main_box.set_margin_start(12)
        main_box.set_margin_end(12)

        content.append(main_box)

        # =========================
        # 1. Host Addr
        # =========================
        host_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        host_label = Gtk.Label(label="Host Addr:")
        host_label.set_xalign(0)

        self.host_entry = Gtk.Entry()
        self.host_entry.set_hexpand(True)
        self.host_entry.set_placeholder_text("https://host_addr")

        host_box.append(host_label)
        host_box.append(self.host_entry)

        main_box.append(host_box)

        # =========================
        # 2. File List
        # =========================
        file_frame = Gtk.Frame(label="Proto Files")

        file_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        file_frame.set_child(file_box)

        # list store
        self.file_store = Gtk.StringList()

        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._file_item_setup)
        factory.connect("bind", self._file_item_bind)

        selection = Gtk.SingleSelection(model=self.file_store)

        listview = Gtk.ListView(model=selection, factory=factory)
        listview.set_vexpand(True)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(listview)
        scrolled.set_vexpand(True)

        file_box.append(scrolled)

        # add button
        add_btn = Gtk.Button(label="+ Add Proto Files")
        add_btn.connect("clicked", self.on_add_files_clicked)

        file_box.append(add_btn)

        main_box.append(file_frame)

        self.settings_window.connect("response", self.on_settings_response)

        self.settings_window.show()

    def _file_item_setup(self, factory, listitem):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        label = Gtk.Label(xalign=0)
        label.set_hexpand(True)

        remove_btn = Gtk.Button(label="✖")
        remove_btn.set_focusable(False)

        row.append(label)
        row.append(remove_btn)

        listitem.set_child(row)

        listitem._label = label
        listitem._btn = remove_btn

    def _file_item_bind(self, factory, listitem):
        item = listitem.get_item()
        if not item:
            return

        text = item.get_string()

        listitem._label.set_text(text)

        def on_remove(btn):
            idx = listitem.get_position()
            self.file_store.remove(idx)

        listitem._btn.connect("clicked", on_remove)

    def on_add_files_clicked(self, btn):
        self._file_dialog = Gtk.FileChooserNative(
            title="Select Files",
            action=Gtk.FileChooserAction.OPEN,
            transient_for=self.settings_window,
        )
        self._file_dialog.set_modal(True)
        self._file_dialog.set_select_multiple(True)
        # self._file_dialog.get_style_context().add_class("settings_window")
        filter_proto = Gtk.FileFilter()
        filter_proto.set_name("Proto Files")
        filter_proto.add_pattern("*.proto")

        self._file_dialog.add_filter(filter_proto)
        self._file_dialog.set_filter(filter_proto)

        def on_response(d, res):
            if res == Gtk.ResponseType.ACCEPT:
                files = d.get_files()
                for f in files:
                    path = f.get_path()
                    self.file_store.append(path)

            d.destroy()

        self._file_dialog.connect("response", on_response)
        self._file_dialog.show()

    def on_settings_response(self, dialog, response):
        if response == Gtk.ResponseType.OK:
            host = self.host_entry.get_text()

            files = []
            for i in range(self.file_store.get_n_items()):
                files.append(self.file_store.get_string(i))

            print("Host:", host)
            print("Files:", files)

        dialog.destroy()

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
