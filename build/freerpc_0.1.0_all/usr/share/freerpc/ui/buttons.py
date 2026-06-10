import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk


def make_icon_text_button(icon_text, label_text, clicked_callback, css):
    btn = Gtk.Button()
    if icon_text != "" and label_text != "":
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        icon = Gtk.Label(label=icon_text)
        box.append(icon)
        label = Gtk.Label(label=label_text)
        box.append(label)
        btn.set_child(box)
    if icon_text != "" and label_text == "":
        label = Gtk.Label(label=icon_text)
        btn.set_child(label)
    if label_text != "" and icon_text == "":
        label = Gtk.Label(label=label_text)
        btn.set_child(label)
    btn.connect("clicked", clicked_callback)
    btn.get_style_context().add_class(css)
    return btn
