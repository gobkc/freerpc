import json

import grpc

from services.grpc_service import dynamic_grpc_call


class CenterPanelHandler:
    def __init__(self, panel):
        self.panel = panel
        self.context = panel.context

    def on_init(self):
        pass

    def on_send_click(self, button):
        try:
            url = self.panel.url_entry.get_text()
            print(f"Send gRPC request to: {url}")
            print(f"request schema: {self.context.request_schema}")
            print(f"rpc info: {self.context.current_rpc}")
            parameter = self.panel.textview.get_data()
            response = dynamic_grpc_call(
                proto_path=self.context.current_rpc["file_path"],
                service_name=self.context.current_rpc["service_name"],
                method_name=self.context.current_rpc["func_name"],
                rpc_type=self.context.current_rpc["type"],
                host=self.context.current_rpc["host"],
                request_dict=parameter,
            )
            response_view_buffer = (
                self.panel.window.right_panel.response_view.get_buffer()
            )
            response_view_buffer.set_text(
                json.dumps(response, indent=2, ensure_ascii=False)
            )
        except grpc.RpcError as e:
            # 获取 gRPC 错误信息
            status_code = e.code()
            details = e.details()
            error_msg = f"faled to call gRPC API\n{status_code}\n{details}"
            response_view_buffer = (
                self.panel.window.right_panel.response_view.get_buffer()
            )
            response_view_buffer.set_text(error_msg)

        except Exception as e:
            # 捕获其他意外错误（可选）
            error_msg = f"发生未知错误: {str(e)}"
            response_view_buffer = (
                self.panel.window.right_panel.response_view.get_buffer()
            )
            response_view_buffer.set_text(error_msg)

    def on_format_json_click(self, button):
        self.panel.textview._manual_render()

    def on_clear_json_click(self, button):
        self.panel.set_json_text("")

    def on_format_meta_click(self, button):
        self.panel.meta_textview._manual_render()

    def on_clear_meta_click(self, button):
        buffer = self.panel.meta_textview.get_buffer()
        buffer.set_text("")
