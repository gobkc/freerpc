import os

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")

from importlib import resources

from gi.repository import Gdk, Gio, Gtk

from context.app_context import AppContext
from ui.main_window import MainWindow


class App(Gtk.Application):
    def __init__(self):
        self.context = AppContext()
        self.context.init()
        super().__init__(application_id="com.py.grpcui")
        self.connect("activate", self.on_activate)

    def on_activate(self, app):
        self.load_css()

        win = MainWindow(application=app, context=self.context)
        win.present()

    def load_css(self):
        provider = Gtk.CssProvider()
        css_path = "styles/style.css"
        loaded = False

        if os.path.exists(css_path):
            try:
                provider.load_from_path(css_path)
                print(f"Loaded CSS from external path: {css_path}")
                loaded = True
            except Exception as e:
                print(f"Error loading external CSS: {e}")

        if not loaded:
            try:
                css_data = resources.files("styles").joinpath("style.css").read_bytes()
                provider.load_from_data(css_data)
                print("Loaded CSS from internal resources (zipapp)")
                loaded = True
            except Exception as e:
                print(f"Internal CSS load error: {e}")

        if not loaded:
            return

        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

    def run(self):
        super().run(None)
