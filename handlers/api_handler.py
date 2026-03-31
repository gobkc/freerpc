class ApiHandler:
    def __init__(self, window):
        self.window = window

    def on_api_selected(self, listbox, row):
        label = row.get_child()
        api_name = label.get_text()

        self.window.center_panel.set_api(api_name)

        # TODO: 根据 proto 生成默认 JSON
        self.window.center_panel.set_json_text("{\n  \n}")
