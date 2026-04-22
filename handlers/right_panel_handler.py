from gi.repository import GLib


class RightPanelHandler:
    def __init__(self, panel):
        self.panel = panel
        self.context = panel.context

    def on_response_view_change(self, text):
        if not hasattr(self.context, "data") or not self.context.data:
            return
        self.context.config = self.context.config_manager.update_rpc_fields(
            package=self.context.data["package"],
            service_name=self.context.data["service_name"],
            func_name=self.context.data["func_name"],
            updates={"result": text},
        )

    def on_log_view_change(self, text):
        if not hasattr(self.context, "data") or not self.context.data:
            return
        self.context.config = self.context.config_manager.update_rpc_fields(
            package=self.context.data["package"],
            service_name=self.context.data["service_name"],
            func_name=self.context.data["func_name"],
            updates={"log": text},
        )

    def on_tab_changed(self, notebook, page, page_num):
        label_widget = notebook.get_tab_label(page)
        if (
            hasattr(label_widget, "get_text")
            and label_widget.get_text() == "Execution Log"
        ):
            log_content = getattr(self.context, "log_buffer", "")
            GLib.timeout_add(100, self._deferred_log_update, log_content)

    def _deferred_log_update(self, content):
        buffer = self.panel.log_view.textview.get_buffer()
        if (
            buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
            != content
        ):
            buffer.set_text(content if content else "")
        return False
