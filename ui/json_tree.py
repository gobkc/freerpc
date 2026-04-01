import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gio", "2.0")

from gi.repository import Gdk, Gio, GObject, Gtk


# =========================
# Tree Node
# =========================
class TreeNode(GObject.Object):
    __gtype_name__ = "TreeNode"

    key = GObject.Property(type=str, default="")
    value = GObject.Property(type=str, default="")
    node_type = GObject.Property(type=str, default="string")
    children = GObject.Property(type=Gio.ListStore)

    def __init__(self, key="", value=None, node_type="string", children=None):
        super().__init__()
        self.key = key
        self.node_type = node_type
        self.children = children or Gio.ListStore()

        if value is not None:
            self.value = str(value)
        else:
            self.value = ""

    def get_python_value(self):
        if self.node_type == "object":
            obj = {}
            for i in range(self.children.get_n_items()):
                c = self.children.get_item(i)
                obj[c.key] = c.get_python_value()
            return obj

        if self.node_type == "array":
            return [
                self.children.get_item(i).get_python_value()
                for i in range(self.children.get_n_items())
            ]

        if self.node_type == "number":
            try:
                return int(self.value)
            except:
                return float(self.value)

        if self.node_type == "bool":
            return self.value.lower() == "true"

        if self.node_type == "null":
            return None

        return self.value


def build_tree(data):
    root = TreeNode(key="root")

    if isinstance(data, dict):
        root.node_type = "object"
        for k, v in data.items():
            child = TreeNode(key=k)
            child._set(v)
            root.children.append(child)

    elif isinstance(data, list):
        root.node_type = "array"
        for v in data:
            child = TreeNode()
            child._set(v)
            root.children.append(child)

    else:
        root._set(data)

    return root


def _set(self, value):
    if isinstance(value, dict):
        self.node_type = "object"
        self.children.remove_all()
        for k, v in value.items():
            c = TreeNode(key=k)
            c._set(v)
            self.children.append(c)

    elif isinstance(value, list):
        self.node_type = "array"
        self.children.remove_all()
        for v in value:
            c = TreeNode()
            c._set(v)
            self.children.append(c)

    elif isinstance(value, bool):
        self.node_type = "bool"
        self.value = "true" if value else "false"

    elif isinstance(value, (int, float)):
        self.node_type = "number"
        self.value = str(value)

    elif value is None:
        self.node_type = "null"
        self.value = "null"

    else:
        self.node_type = "string"
        self.value = str(value)


TreeNode._set = _set


# =========================
# UI Item Row
# =========================
class TreeItemBox(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        self.expander = Gtk.TreeExpander()
        self.append(self.expander)

        self.icon = Gtk.Label()
        self.icon.set_width_chars(2)
        self.append(self.icon)

        self.label = Gtk.Label(xalign=0)
        self.label.set_hexpand(True)
        self.append(self.label)


# =========================
# JsonTree Widget
# =========================
class JsonTree(Gtk.ScrolledWindow):
    __gsignals__ = {
        "node-activated": (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        "node-right-click": (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }

    def __init__(self, editable=False):
        super().__init__()

        self.editable = editable

        self.model = None
        self.selection = Gtk.SingleSelection()

        self.list_view = Gtk.ListView()
        self.set_child(self.list_view)

        self.factory = Gtk.SignalListItemFactory()
        self.factory.connect("setup", self._setup)
        self.factory.connect("bind", self._bind)

        self.list_view.set_factory(self.factory)

        self.selection.set_model(None)
        self.list_view.set_model(self.selection)

        self.list_view.connect("activate", self._on_activate)

    # -------------------------
    # PUBLIC API
    # -------------------------
    def set_data(self, data):
        root = build_tree(data)

        store = Gio.ListStore()
        store.append(root)

        self.model = Gtk.TreeListModel.new(
            store,
            False,
            False,
            self._create_child_model,
        )

        self.selection.set_model(self.model)

    def get_json(self):
        if self.model:
            root = self.model.get_model().get_item(0)
            return root.get_python_value()
        return None

    # -------------------------
    # TREE MODEL
    # -------------------------
    def _create_child_model(self, item):
        if item.node_type in ("object", "array"):
            return item.children
        return None

    # -------------------------
    # UI
    # -------------------------
    def _setup(self, factory, listitem):
        box = TreeItemBox()
        listitem.set_child(box)

        # ❗ GTK4正确方式：直接挂 Python 属性
        listitem._box = box

        if self.editable:
            gesture = Gtk.GestureClick()
            gesture.set_button(3)
            gesture.connect("pressed", self._on_right_click, listitem)
            box.add_controller(gesture)

    def _bind(self, factory, listitem):
        row = listitem.get_item()
        if not row:
            return

        item = row.get_item()  # ⭐ 关键！

        box = listitem._box

        box.expander.set_list_row(row)

        # icon
        if item.node_type == "object":
            box.icon.set_text("📁")
        elif item.node_type == "array":
            box.icon.set_text("📦")
        else:
            box.icon.set_text("•")

        # label
        text = item.key
        if item.node_type not in ("object", "array"):
            text += f": {item.value}"

        box.label.set_text(text)

    # -------------------------
    # EVENTS
    # -------------------------
    def _on_activate(self, listview, pos):
        row = self.selection.get_selected_item()
        if row:
            item = row.get_item()
            self.emit("node-activated", item)

    def _on_right_click(self, gesture, n, x, y, listitem):
        row = listitem.get_item()
        if row:
            item = row.get_item()
            self.emit("node-right-click", item)
