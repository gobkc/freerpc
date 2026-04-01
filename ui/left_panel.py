import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gio, Gtk

from ui.json_tree import JsonTree


class LeftPanel(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.window = window
        self.set_margin_top(6)
        self.set_margin_bottom(6)
        self.set_margin_start(6)
        self.set_margin_end(6)

        label = Gtk.Label(label="Proto & APIs")
        self.append(label)

        # 使用 JsonTree 展示 API 树（只读，不显示图标或编辑）
        self.tree = JsonTree(editable=False)
        self.tree.set_vexpand(True)
        self.tree.connect("node-activated", self._on_api_selected)
        self.append(self.tree)

        # 示例数据：手动构建 API 树
        self.load_demo_apis()

    def load_demo_apis(self):
        """从 proto 解析或硬编码构建 API 树"""
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
        """当 API 节点被双击或 Enter 时触发"""
        # 获取节点对应的 Python 值，例如 {"request": {...}}
        api_info = node.get_python_value()
        if isinstance(api_info, dict):
            # 假设叶子节点是方法，其值包含 request 字段
            request_template = api_info.get("request", {})
            # 通知主窗口切换 API
            self.window.center_panel.set_api(node.key, request_template)
