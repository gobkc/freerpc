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
    depth = GObject.Property(type=int, default=0)  # 新增深度属性

    def __init__(self, key="", value=None, node_type="string", children=None, depth=0):
        super().__init__()
        self.key = key
        self.node_type = node_type
        self.children = children or Gio.ListStore()
        self.depth = depth

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


def build_tree(data, current_depth=0):
    """构建树，current_depth 为当前节点深度（根节点深度为 0）"""
    root = TreeNode(key="root", depth=current_depth)

    if isinstance(data, dict):
        root.node_type = "object"
        for k, v in data.items():
            child = TreeNode(key=k, depth=current_depth + 1)
            child._set(v, current_depth + 1)
            root.children.append(child)

    elif isinstance(data, list):
        root.node_type = "array"
        for v in data:
            child = TreeNode(depth=current_depth + 1)
            child._set(v, current_depth + 1)
            root.children.append(child)

    else:
        root._set(data, current_depth)

    return root


def _set(self, value, depth):
    """递归设置节点值，depth 为当前节点深度"""
    self.depth = depth
    if isinstance(value, dict):
        self.node_type = "object"
        self.children.remove_all()
        for k, v in value.items():
            c = TreeNode(key=k, depth=depth + 1)
            c._set(v, depth + 1)
            self.children.append(c)

    elif isinstance(value, list):
        self.node_type = "array"
        self.children.remove_all()
        for v in value:
            c = TreeNode(depth=depth + 1)
            c._set(v, depth + 1)
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
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)

        self.expander = Gtk.TreeExpander()
        self.append(self.expander)

        self.icon = Gtk.Label()
        self.icon.set_width_chars(0)  # 2
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

    def __init__(self, editable=False, depth=None):
        """
        :param editable: 是否允许右键编辑（目前仅预留手势）
        :param depth: 显示的最大深度，None 表示不限制，1 表示仅显示第一层（不可展开），
                      2 表示可展开第一层子项，以此类推。
        """
        super().__init__()
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.set_propagate_natural_width(True)
        self.editable = editable
        self.max_depth = depth  # None 或正整数

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
        root = build_tree(data, current_depth=0)

        store = Gio.ListStore()
        for child in root.children:
            store.append(child)
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
        # 深度限制：如果设置了 max_depth 且当前节点深度已达到或超过最大深度，则不生成子模型
        if self.max_depth is not None and item.depth >= self.max_depth:
            return None
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
        has_children = item.node_type in ("object", "array")
        if has_children:
            # 即使有子节点，如果深度限制导致无法展开，也不显示展开指示符
            can_expand = self.max_depth is None or item.depth < self.max_depth
            if can_expand and row.get_expanded():
                box.icon.set_text("−")
            elif can_expand:
                box.icon.set_text("+")
            else:
                box.icon.set_text("")  # 达到深度限制，不显示展开符号
        else:
            box.icon.set_text("")

        # icon
        if item.node_type == "object":
            box.icon.set_text("")
            # box.icon.set_text("📁")
        elif item.node_type == "array":
            box.icon.set_text("")
            # box.icon.set_text("＋")
        else:
            box.icon.set_text("")
            # box.icon.set_text("•")

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
