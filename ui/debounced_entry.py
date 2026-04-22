import gi

gi.require_version("Gtk", "4.0")
from gi.repository import GLib, Gtk


class DebouncedEntry(Gtk.Entry):
    def __init__(self, delay=500):
        super().__init__()

        self._debounce_delay = delay
        self._debounce_id = None
        self._callback = None

        self.connect("changed", self._on_changed)

    def _on_changed(self, entry):
        if self._debounce_id:
            GLib.source_remove(self._debounce_id)

        self._debounce_id = GLib.timeout_add(self._debounce_delay, self._emit_debounced)

    def _emit_debounced(self):
        self._debounce_id = None

        if self._callback:
            text = self.get_text()
            try:
                self._callback(text)
            except Exception as e:
                print("error:", e)
                pass

        return False

    def connect_debounced_changed(self, callback, delay=None):
        self._callback = callback
        if delay is not None:
            self._debounce_delay = delay
