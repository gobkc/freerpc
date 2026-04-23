import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk

from ui.center_panel import CenterPanel
from ui.header_bar import HeaderBar
from ui.left_panel import LeftPanel
from ui.right_panel import RightPanel


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, application, context):
        self.context = context
        super().__init__(application=application)
        headerbar = Gtk.HeaderBar()
        headerbar.set_show_title_buttons(True)
        headerbar.set_title_widget(Gtk.Label(label="freerpc——gRPC UI Client"))
        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", True)
        self.set_titlebar(headerbar)
        self.set_default_size(1200, 800)

        # ✅ 启动时最大化
        self.maximize()

        # 主垂直布局
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox.add_css_class("full-box")
        vbox.set_hexpand(True)
        vbox.set_vexpand(True)
        self.set_child(vbox)
        vbox.get_style_context().add_class("main")

        # =========================
        # ✅ 下半部分：Paned结构
        # =========================

        # 左 + (中+右)
        paned_main = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.append(paned_main)

        # 中 + 右
        paned_right = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)

        # 创建三个面板
        self.left_panel = LeftPanel(self)
        self.left_panel.get_style_context().add_class("left_panel")
        self.center_panel = CenterPanel(self)
        self.right_panel = RightPanel(self)
        self.right_panel.get_style_context().add_class("right_panel")

        # 包装滚动（重点）
        left_scroll = self.wrap_scroll(self.left_panel, hpolicy=Gtk.PolicyType.NEVER)
        center_scroll = self.wrap_scroll(self.center_panel)
        right_scroll = self.wrap_scroll(self.right_panel)

        # 组装
        paned_main.set_start_child(left_scroll)
        paned_main.set_end_child(paned_right)

        paned_right.set_start_child(center_scroll)
        paned_right.set_end_child(right_scroll)

        # 默认分割比例
        paned_main.set_position(250)
        paned_right.set_position(600)

    def wrap_scroll(self, widget, hpolicy=Gtk.PolicyType.AUTOMATIC):
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(widget)

        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        scrolled.set_policy(hpolicy, Gtk.PolicyType.AUTOMATIC)
        return scrolled
