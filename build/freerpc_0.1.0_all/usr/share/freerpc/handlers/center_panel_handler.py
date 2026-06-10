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

    # --- 线程安全的 UI 更新辅助方法 ---
    def _set_buffer_text(self, buffer, text):
        """通用 Buffer 更新方法，由 idle_add 调用"""
        buffer.set_text(text if text else "")
        return False  # 返回 False 保证只执行一次

    def _safe_update_response(self, text):
        buf = self.panel.window.right_panel.response_view.textview.get_buffer()
        GLib.idle_add(self._set_buffer_text, buf, text)

    def _safe_update_log(self, text):
        buf = self.panel.window.right_panel.log_view.textview.get_buffer()
        GLib.idle_add(self._set_buffer_text, buf, text)

    # --- 事件处理 ---
    def on_send_click(self, button):
        url = self.panel.url_entry.get_text()
        parameter = self.panel.parameter.get_dict()
        metadata = self.panel.meta_textview.get_dict()
        rpc_info = self.context.current_rpc

        if not rpc_info:
            return

        self._safe_update_response("Requesting...")
        self._safe_update_log("Waiting for execution details...")

        thread = threading.Thread(
            target=self._execute_grpc_call,
            args=(url, parameter, metadata, rpc_info),
            daemon=True,
        )
        thread.start()

    def _execute_grpc_call(self, url, parameter, metadata, rpc_info):
        def details_handler(details):
            self._safe_update_log(details)

        try:
            rpc_type_str = rpc_info["type"].strip().lower()
            is_client_stream = (
                "client" in rpc_type_str or "bidirectional" in rpc_type_str
            )
            is_server_stream = (
                "server" in rpc_type_str or "bidirectional" in rpc_type_str
            )
            req_dict: Dict[str, Any] = {}
            req_stream = None

            if is_client_stream:
                req_stream = parameter if isinstance(parameter, list) else [parameter]
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
                details_callback=details_handler,
            )
            if is_server_stream:
                results = []
                for resp_item in response:
                    results.append(resp_item)
                display_text = json.dumps(results, indent=2, ensure_ascii=False)
            else:
                display_text = json.dumps(response, indent=2, ensure_ascii=False)

            self._safe_update_response(display_text)

        except grpc.RpcError as e:
            error_msg = f"gRPC Error:\nCode: {e.code()}\nDetails: {e.details()}"
            self._safe_update_response(error_msg)
        except Exception as e:
            error_msg = f"Internal Exception:\n{str(e)}"
            self._safe_update_response(error_msg)

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

    def on_host_change(self, text):
        self.context.config = self.context.config_manager.update_rpc_fields(
            package=self.context.data["package"],
            service_name=self.context.data["service_name"],
            func_name=self.context.data["func_name"],
            updates={
                "host": text,
            },
        )
        print("host debounced changed:", text)

    def on_parameter_change(self, text):
        self.context.config = self.context.config_manager.update_rpc_fields(
            package=self.context.data["package"],
            service_name=self.context.data["service_name"],
            func_name=self.context.data["func_name"],
            updates={
                "parameters": text,
            },
        )
        print("parameter debounced changed:", text)

    def on_metadata_change(self, text):
        self.context.config = self.context.config_manager.update_rpc_fields(
            package=self.context.data["package"],
            service_name=self.context.data["service_name"],
            func_name=self.context.data["func_name"],
            updates={
                "metadata": text,
            },
        )
        print("debounced changed:", text)
