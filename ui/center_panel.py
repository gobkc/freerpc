import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk


class CenterPanel(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        self.window = window
        self.set_margin_top(6)
        self.set_margin_bottom(6)
        self.set_margin_start(6)
        self.set_margin_end(6)

        # 标题
        self.api_label = Gtk.Label(label="Select an API")
        self.append(self.api_label)

        # JSON 输入
        self.textview = Gtk.TextView()
        self.textview.set_vexpand(True)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self.textview)
        self.append(scrolled)

        # Meta 信息
        meta_label = Gtk.Label(label="Metadata")
        self.append(meta_label)

        self.meta_entry = Gtk.Entry()
        self.append(self.meta_entry)

        # 发送按钮
        send_btn = Gtk.Button(label="Send Request")
        send_btn.connect("clicked", self.on_send_clicked)
        self.append(send_btn)

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
        print("Send gRPC request (TODO)")
