import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")

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

        try:
            provider.load_from_path("styles/style.css")
        except Exception as e:
            print("CSS load error:", e)
            return

        display = Gdk.Display.get_default()

        Gtk.StyleContext.add_provider_for_display(
            display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def run(self):
        super().run(None)
