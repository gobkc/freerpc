import json
import threading
from typing import Any, Dict

import grpc
from gi.repository import GLib

from services.grpc_service import dynamic_grpc_call


class CenterPanelHandler:
    def __init__(self, panel):
        self.panel = panel
        self.context = panel.context

    def on_init(self):
        pass

    def update_ui_buffer(self, text):
        response_view_buffer = (
            self.panel.window.right_panel.response_view.textview.get_buffer()
        )
        response_view_buffer.set_text(text)
        return False

    def on_send_click(self, button):
        url = self.panel.url_entry.get_text()
        parameter = self.panel.parameter.get_dict()
        metadata = self.panel.meta_textview.get_dict()
        rpc_info = self.context.current_rpc

        if not rpc_info:
            return

        self.update_ui_buffer("Requesting...")

        thread = threading.Thread(
            target=self._execute_grpc_call,
            args=(url, parameter, metadata, rpc_info),
            daemon=True,
        )
        thread.start()

    def _execute_grpc_call(self, url, parameter, metadata, rpc_info):
        try:
            rpc_type_str = rpc_info["type"].strip().lower()
            is_client_stream = rpc_type_str in (
                "client streaming",
                "client_streaming",
                "bidirectional",
                "bidirectional streaming",
                "bidirectional_streaming",
            )
            is_server_stream = rpc_type_str in (
                "server streaming",
                "server_streaming",
                "bidirectional",
                "bidirectional streaming",
                "bidirectional_streaming",
            )

            req_dict: Dict[str, Any] = {}
            req_stream = None

            if is_client_stream:
                if isinstance(parameter, list):
                    req_stream = parameter
                else:
                    req_stream = [parameter]
            else:
                if isinstance(parameter, list):
                    req_dict = parameter[0] if len(parameter) > 0 else {}
                else:
                    req_dict = parameter if isinstance(parameter, dict) else {}

            response = dynamic_grpc_call(
                proto_path=rpc_info["file_path"],
                service_name=rpc_info["service_name"],
                method_name=rpc_info["func_name"],
                rpc_type=rpc_type_str,
                host=url,
                request_dict=req_dict,
                request_stream=req_stream,
                metadata=metadata,
            )

            if is_server_stream:
                results = []
                for resp_item in response:
                    results.append(resp_item)
                display_text = json.dumps(results, indent=2, ensure_ascii=False)
            else:
                display_text = json.dumps(response, indent=2, ensure_ascii=False)

            GLib.idle_add(self.update_ui_buffer, display_text)

        except grpc.RpcError as e:
            error_msg = f"failed to call gRPC API\n{e.code()}\n{e.details()}"
            GLib.idle_add(self.update_ui_buffer, error_msg)
        except Exception as e:
            error_msg = f"发生未知错误: {str(e)}"
            GLib.idle_add(self.update_ui_buffer, error_msg)

    def on_format_json_click(self, button):
        self.panel.parameter.format_all_json_content()

    def on_clear_json_click(self, button):
        buffer = self.panel.parameter.textview.get_buffer()
        buffer.set_text(
            json.dumps(self.context.request_schema, indent=2, ensure_ascii=False)
        )

    def on_format_meta_click(self, button):
        self.panel.meta_textview.format_all_json_content()

    def on_clear_meta_click(self, button):
        buffer = self.panel.meta_textview.textview.get_buffer()
        buffer.set_text("{}")
