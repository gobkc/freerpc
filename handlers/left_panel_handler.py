import json

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from services.proto_service import ProtoService


class LeftPanelHandler:
    def __init__(self, panel):
        self.panel = panel
        self.context = panel.context

    # =========================
    # Settings Dialog
    # =========================
    def show_settings_form(self, btn):
        panel = self.panel

        panel.settings_window = Gtk.Dialog(
            title="Settings",
            transient_for=panel.window,
        )
        panel.settings_window.get_style_context().add_class("settings_window")
        panel.settings_window.set_default_size(600, 400)
        panel.settings_window.set_modal(True)
        # panel.get_style_context().add_css_class("settings_window")

        panel.settings_window.add_button("Cancel", Gtk.ResponseType.CANCEL)
        panel.settings_window.add_button("OK", Gtk.ResponseType.OK)

        content = panel.settings_window.get_content_area()

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.set_margin_top(12)
        main_box.set_margin_bottom(12)
        main_box.set_margin_start(12)
        main_box.set_margin_end(12)

        content.append(main_box)

        # =========================
        # Host
        # =========================
        host_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        host_label = Gtk.Label(label="Host Addr:")
        host_label.set_xalign(0)

        panel.host_entry = Gtk.Entry()
        panel.host_entry.set_hexpand(True)
        panel.host_entry.set_placeholder_text("https://host_addr")
        panel.host_entry.set_text(self.context.config.get("host", ""))

        host_box.append(host_label)
        host_box.append(panel.host_entry)

        main_box.append(host_box)

        # =========================
        # File List
        # =========================
        file_frame = Gtk.Frame(label="Proto Files")

        file_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        file_frame.set_child(file_box)

        panel.file_store = Gtk.StringList()
        protos = self.context.config.get("protos", [])
        for proto in protos:
            path = proto.get("path")
            if path:
                panel.file_store.append(path)

        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._file_item_setup)
        factory.connect("bind", self._file_item_bind)

        selection = Gtk.SingleSelection(model=panel.file_store)

        listview = Gtk.ListView(model=selection, factory=factory)
        listview.set_vexpand(True)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(listview)
        scrolled.set_vexpand(True)

        file_box.append(scrolled)

        add_btn = Gtk.Button(label="+ Add Proto Files")
        add_btn.connect("clicked", self.on_add_files_clicked)

        file_box.append(add_btn)

        main_box.append(file_frame)

        panel.settings_window.connect("response", self.on_click_settings_ok)
        panel.settings_window.show()

    def on_left_tree_init(self):
        config = self.panel.context.config
        tree_data = {}
        protos = config.get("protos", [])
        for proto in protos:
            services = proto.get("services", [])
            for service in services:
                service_name = service.get("name", "UnknownService")
                if service_name not in tree_data:
                    tree_data[service_name] = {}
                rpcs = service.get("rpc", [])
                for rpc in rpcs:
                    func_name = rpc.get("func", "UnknownFunc")
                    request_schema = rpc.get("request_schema", {})
                    tree_data[service_name][func_name] = {"request": request_schema}
        if not tree_data:
            tree_data = {}
        self.panel.tree.set_data(tree_data)

    # =========================
    # List Item UI
    # =========================
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

        # ⚠️ 防止重复绑定（GTK4坑）
        if hasattr(listitem, "_handler_id"):
            listitem._btn.disconnect(listitem._handler_id)

        def on_remove(btn):
            idx = listitem.get_position()
            self.panel.file_store.remove(idx)

        handler_id = listitem._btn.connect("clicked", on_remove)
        listitem._handler_id = handler_id

    # =========================
    # File chooser
    # =========================
    def on_add_files_clicked(self, btn):
        panel = self.panel

        panel._file_dialog = Gtk.FileChooserNative(
            title="Select Files",
            action=Gtk.FileChooserAction.OPEN,
            transient_for=panel.settings_window,
        )
        panel._file_dialog.set_modal(True)
        panel._file_dialog.set_select_multiple(True)

        filter_proto = Gtk.FileFilter()
        filter_proto.set_name("Proto Files")
        filter_proto.add_pattern("*.proto")

        panel._file_dialog.add_filter(filter_proto)
        panel._file_dialog.set_filter(filter_proto)

        panel._file_dialog.connect("response", self._on_file_dialog_response)
        panel._file_dialog.show()

    def _on_file_dialog_response(self, dialog, response):
        panel = self.panel

        if response == Gtk.ResponseType.ACCEPT:
            files = dialog.get_files()
            for f in files:
                path = f.get_path()
                panel.file_store.append(path)

        dialog.destroy()

    # =========================
    # Settings submit
    # =========================
    def on_click_settings_ok(self, dialog, response):
        panel = self.panel
        config = self.context.config

        if response == Gtk.ResponseType.OK:
            host = panel.host_entry.get_text()
            files = []
            for i in range(panel.file_store.get_n_items()):
                files.append(panel.file_store.get_string(i))
            # parse protos
            files = list(set(files))
            protos = []
            for f in files:
                try:
                    proto = ProtoService.parse_proto_file(f)
                    protos.append(proto)
                except Exception as e:
                    print(f"Parse proto failed: {f}, error: {e}")
            self.context.config["host"] = host
            self.context.config["protos"] = protos
            self.context.config_manager.set_config(config)
            print("Updated Config:", json.dumps(self.context.config))
            self.on_left_tree_init()

        dialog.destroy()

    # =========================
    # API click
    # =========================
    def on_api_selected(self, tree, node):
        panel = self.panel

        api_info = node.get_python_value()
        if isinstance(api_info, dict):
            request_template = api_info.get("request", {})
            panel.window.center_panel.set_api(node.key, request_template)
