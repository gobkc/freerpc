import gi

from ui.debounced_entry import DebouncedEntry
from ui.json_gutter_renderer import JsonGutterRenderer

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk

from handlers.center_panel_handler import CenterPanelHandler
from ui.editable_json_tree import EditableJsonTree


class CenterPanel(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self.window = window
        self.context = window.context
        self.handler = CenterPanelHandler(self)

        top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

        self.url_entry = DebouncedEntry(delay=600)
        self.url_entry.set_placeholder_text("https://host_addr")
        self.url_entry.set_hexpand(True)
        self.url_entry.connect_debounced_changed(self.handler.on_host_change)

        send_btn = Gtk.Button(label="Send Request")
        send_btn.get_style_context().add_class("important_btn")
        send_btn.connect("clicked", self.handler.on_send_click)

        top_bar.append(self.url_entry)
        top_bar.append(send_btn)

        self.append(top_bar)

        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.rpc_type_label = self.create_section_label("[Unknown]")
        self.rpc_type_label.set_name("rpc-type-label")
        self.rpc_type_label.set_hexpand(False)
        header_box.append(self.rpc_type_label)
        self.api_label = self.create_section_label(" Select an API")
        self.api_label.set_margin_start(0)
        header_box.append(self.api_label)

        format_btn = Gtk.Button(label="{/}")
        format_btn.get_style_context().add_class("icon_btn")
        format_btn.set_tooltip_text("format JSON")
        format_btn.connect("clicked", self.handler.on_format_json_click)

        header_box.append(format_btn)

        clear_btn = Gtk.Button(label="×")
        clear_btn.get_style_context().add_class("icon_btn")
        clear_btn.set_tooltip_text("clear contents")
        clear_btn.connect("clicked", self.handler.on_clear_json_click)

        header_box.append(clear_btn)

        self.append(header_box)

        paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        paned.get_style_context().add_class("parameter_paned")
        paned.set_vexpand(True)

        self.parameter = JsonGutterRenderer(theme="dark", show_line_numbers=False)
        self.parameter.get_style_context().add_class("json_gutter")
        self.parameter.textview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.parameter.connect_debounced_changed(
            self.handler.on_parameter_change, delay=800
        )

        json_scrolled = Gtk.ScrolledWindow()
        json_scrolled.set_overlay_scrolling(False)
        json_scrolled.set_child(self.parameter)
        json_scrolled.set_vexpand(True)

        paned.set_start_child(json_scrolled)

        meta_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        meta_header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        meta_label = self.create_section_label(" Metadata")
        meta_header_box.append(meta_label)

        meta_format_btn = Gtk.Button(label="{/}")
        meta_format_btn.get_style_context().add_class("icon_btn")
        meta_format_btn.set_tooltip_text("format JSON")
        meta_format_btn.connect("clicked", self.handler.on_format_meta_click)

        meta_header_box.append(meta_format_btn)

        meta_clear_btn = Gtk.Button(label="×")
        meta_clear_btn.get_style_context().add_class("icon_btn")
        meta_clear_btn.set_tooltip_text("clear contents")
        meta_clear_btn.connect("clicked", self.handler.on_clear_meta_click)

        meta_header_box.append(meta_clear_btn)
        meta_header_box.add_css_class("meta_box")

        meta_container.append(meta_header_box)

        self.meta_textview = JsonGutterRenderer(theme="dark", show_line_numbers=False)
        self.meta_textview.get_style_context().add_class("json_gutter")
        self.meta_textview.textview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.meta_textview.connect_debounced_changed(
            self.handler.on_metadata_change, delay=800
        )

        meta_scrolled = Gtk.ScrolledWindow()
        meta_scrolled.set_overlay_scrolling(False)
        meta_scrolled.set_child(self.meta_textview)
        meta_scrolled.set_vexpand(True)

        meta_container.append(meta_scrolled)

        paned.set_end_child(meta_container)

        self.append(paned)

        self.handler.on_init()

    def set_api(self, api_name):
        self.api_label.set_text(f"API: {api_name}")

    def get_json_text(self):
        buffer = self.parameter.textview.get_buffer()
        start, end = buffer.get_bounds()
        return buffer.get_text(start, end, True)

    def set_json_text(self, text):
        buffer = self.parameter.textview.get_buffer()
        buffer.set_text(text)

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
