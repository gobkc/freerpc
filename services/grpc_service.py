import datetime
import gzip
import importlib
import json
import os
import shutil
import sys
import tempfile
import time
from typing import Any, Callable, Dict, Generator, Iterable, Optional, Union

import grpc
from google.protobuf.json_format import MessageToDict, ParseDict
from grpc_tools import protoc


def _find_protobuf_include() -> Optional[str]:
    candidates = [
        "/usr/include",
        "/usr/local/include",
        os.path.join(sys.prefix, "include"),
    ]
    try:
        import grpc_tools

        grpc_tools_dir = os.path.dirname(grpc_tools.__file__)
        proto_subdir = os.path.join(grpc_tools_dir, "_proto")
        candidates.append(proto_subdir)
        candidates.append(grpc_tools_dir)
    except ImportError:
        pass
    for candidate in candidates:
        test_path = os.path.join(candidate, "google", "protobuf", "any.proto")
        if os.path.exists(test_path):
            return candidate
    return None


def dynamic_grpc_call(
    proto_path: str,
    service_name: str,
    method_name: str,
    rpc_type: str,
    host: str,
    request_dict: Dict[str, Any],
    request_stream: Optional[Iterable[Dict[str, Any]]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    details_callback: Optional[
        Callable[[str], None]
    ] = None,  # 新增：用于接收详情的回调函数
) -> Union[Dict[str, Any], Generator[Dict[str, Any], None, None]]:

    rpc_type = rpc_type.strip().lower()
    if rpc_type == "unary":
        mode = "unary"
    elif rpc_type in ("server streaming", "server_streaming"):
        mode = "server_streaming"
    elif rpc_type in ("client streaming", "client_streaming"):
        mode = "client_streaming"
    elif rpc_type in (
        "bidirectional streaming",
        "bidirectional",
        "bidirectional_streaming",
    ):
        mode = "bidirectional"
    else:
        raise ValueError(f"Invalid rpc_type: {rpc_type}")

    proto_path = os.path.abspath(proto_path)
    proto_dir = os.path.dirname(proto_path)
    proto_filename = os.path.basename(proto_path)
    module_base = os.path.splitext(proto_filename)[0]
    temp_dir = tempfile.mkdtemp()

    protoc_args = [
        "grpc_tools.protoc",
        f"--proto_path={proto_dir}",
        f"--python_out={temp_dir}",
        f"--grpc_python_out={temp_dir}",
        proto_filename,
    ]
    include_dir = _find_protobuf_include()
    if include_dir:
        protoc_args.insert(2, f"--proto_path={include_dir}")
    else:
        print(
            "Warning: Could not find protobuf include directory. Compilation may fail.",
            file=sys.stderr,
        )

    if protoc.main(protoc_args) != 0:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError(f"Failed to compile {proto_path}")

    sys.path.insert(0, temp_dir)
    try:
        pb2_module = importlib.import_module(f"{module_base}_pb2")
        pb2_grpc_module = importlib.import_module(f"{module_base}_pb2_grpc")
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError(f"Import failed: {e}") from e

    def cleanup():
        if temp_dir in sys.path:
            sys.path.remove(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)

    def find_stub_class(module, service_name: str):
        # (保持原有逻辑不变...)
        stub_name = f"{service_name}Stub"
        stub_class = getattr(module, stub_name, None)
        if stub_class:
            return stub_class
        if service_name:
            capitalized = service_name[0].upper() + service_name[1:]
            stub_name = f"{capitalized}Stub"
            stub_class = getattr(module, stub_name, None)
            if stub_class:
                return stub_class
        if "." in service_name:
            simple = service_name.split(".")[-1]
            if simple:
                capitalized = simple[0].upper() + simple[1:]
                stub_name = f"{capitalized}Stub"
                stub_class = getattr(module, stub_name, None)
                if stub_class:
                    return stub_class
        all_stubs = [attr for attr in dir(module) if attr.endswith("Stub")]
        if len(all_stubs) == 1:
            return getattr(module, all_stubs[0])
        elif len(all_stubs) > 1:
            raise RuntimeError(
                f"Multiple Stub classes found: {all_stubs}. "
                f"Please specify the correct service_name (e.g., '{all_stubs[0][:-4]}')."
            )
        else:
            available = [a for a in dir(module) if not a.startswith("_")]
            raise RuntimeError(f"No Stub class found. Available names: {available}")

    stub_class = find_stub_class(pb2_grpc_module, service_name)

    def find_message_class(suffix_hint: str) -> type:
        # (保持原有逻辑不变...)
        request_suffixes = ["Request", "Req", "RequestMsg"]
        response_suffixes = ["Response", "Reply", "Resp", "ResponseMsg"]
        suffixes = request_suffixes if suffix_hint == "Request" else response_suffixes

        candidates = []
        for attr in dir(pb2_module):
            cls = getattr(pb2_module, attr)
            if not isinstance(cls, type):
                continue
            if method_name.lower() not in attr.lower():
                continue
            for suf in suffixes:
                if attr.endswith(suf):
                    candidates.append((attr, cls))
                    break

        if len(candidates) == 1:
            return candidates[0][1]
        elif len(candidates) > 1:
            for attr, cls in candidates:
                if attr.endswith(suffix_hint):
                    return cls
            raise RuntimeError(
                f"Multiple possible {suffix_hint} classes for method {method_name}: "
                f"{[c[0] for c in candidates]}. Please ensure unique naming."
            )
        else:
            all_msg_classes = [
                attr
                for attr in dir(pb2_module)
                if isinstance(getattr(pb2_module, attr), type)
                and not attr.startswith("_")
            ]
            raise RuntimeError(
                f"Cannot find {suffix_hint} message class for method {method_name}. "
                f"Available message classes: {all_msg_classes}"
            )

    req_class = find_message_class("Request")
    resp_class = find_message_class("Response")

    def dict_to_msg(d: Dict[str, Any]):
        msg = req_class()
        ParseDict(d, msg)
        return msg

    def msg_to_dict(m):
        return MessageToDict(m, preserving_proto_field_name=True)

    grpc_metadata = []
    if metadata:
        for k, v in metadata.items():
            val = v if isinstance(v, (str, bytes)) else json.dumps(v)
            grpc_metadata.append((k, val))

    channel = grpc.insecure_channel(host, options=[("grpc.http_proxy", "")])
    stub = stub_class(channel)
    method = getattr(stub, method_name)

    # ================= 新增：详情字符串生成器 =================
    def _trigger_details(
        start_t,
        end_t,
        start_dt,
        end_dt,
        req_msg,
        resp_msg,
        req_dict_data,
        resp_dict_data,
    ):
        if not details_callback:
            return

        duration_ms = (end_t - start_t) * 1000

        req_bytes = req_msg.SerializeToString() if req_msg else b""
        req_hex = req_bytes.hex()
        req_comp = gzip.compress(req_bytes).hex() if req_bytes else ""

        resp_bytes = resp_msg.SerializeToString() if resp_msg else b""
        resp_hex = resp_bytes.hex()

        details = f"""[Request Info]
Time Start: {start_dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]}
Time End:   {end_dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]}
Duration:   {duration_ms:.3f} ms

[Request Data]
Original Dict:
{json.dumps(req_dict_data, indent=2, ensure_ascii=False) if req_dict_data else "{}"}

Protobuf Message:
{str(req_msg).strip() if req_msg else "<Empty>"}

Serialized Bytes (hex):
{req_hex or "<Empty>"}

Simulated Compressed (gzip, hex):
{req_comp or "<Empty>"}

[Response Data]
Raw Bytes (hex):
{resp_hex or "<Empty>"}

Parsed Dict:
{json.dumps(resp_dict_data, indent=2, ensure_ascii=False) if resp_dict_data else "{}"}

[Transport]
Target: {host}
Protocol: gRPC over HTTP/2
Encoding: protobuf
Compression: none (simulated gzip shown above)
Metadata:
{grpc_metadata}

[RPC Info]
Service: {service_name}
Method: {method_name}
Type: {mode}"""

        details_callback(details)

    # ========================================================

    if mode == "unary":
        try:
            req = dict_to_msg(request_dict)
            start_dt = datetime.datetime.now()
            start_t = time.perf_counter()

            resp = method(req, metadata=grpc_metadata)

            end_t = time.perf_counter()
            end_dt = datetime.datetime.now()
            parsed_resp = msg_to_dict(resp)

            _trigger_details(
                start_t, end_t, start_dt, end_dt, req, resp, request_dict, parsed_resp
            )
            return parsed_resp
        finally:
            cleanup()

    elif mode == "server_streaming":
        req = dict_to_msg(request_dict)

        def server_gen():
            start_dt = datetime.datetime.now()
            start_t = time.perf_counter()
            first_resp = None
            first_resp_dict = None

            try:
                for resp in method(req, metadata=grpc_metadata):
                    parsed = msg_to_dict(resp)
                    if first_resp is None:
                        first_resp = resp
                        first_resp_dict = parsed
                    yield parsed
            finally:
                end_t = time.perf_counter()
                end_dt = datetime.datetime.now()
                _trigger_details(
                    start_t,
                    end_t,
                    start_dt,
                    end_dt,
                    req,
                    first_resp,
                    request_dict,
                    first_resp_dict,
                )
                cleanup()

        return server_gen()

    elif mode == "client_streaming":
        first_req = None
        first_req_dict = None

        def req_gen():
            nonlocal first_req, first_req_dict
            if request_stream is not None:
                for d in request_stream:
                    msg = dict_to_msg(d)
                    if first_req is None:
                        first_req = msg
                        first_req_dict = d
                    yield msg
            else:
                msg = dict_to_msg(request_dict)
                first_req = msg
                first_req_dict = request_dict
                yield msg

        try:
            start_dt = datetime.datetime.now()
            start_t = time.perf_counter()

            resp = method(req_gen(), metadata=grpc_metadata)

            end_t = time.perf_counter()
            end_dt = datetime.datetime.now()
            parsed_resp = msg_to_dict(resp)

            _trigger_details(
                start_t,
                end_t,
                start_dt,
                end_dt,
                first_req,
                resp,
                first_req_dict,
                parsed_resp,
            )
            return parsed_resp
        finally:
            cleanup()

    elif mode == "bidirectional":
        first_req = None
        first_req_dict = None

        def req_gen():
            nonlocal first_req, first_req_dict
            if request_stream is not None:
                for d in request_stream:
                    msg = dict_to_msg(d)
                    if first_req is None:
                        first_req = msg
                        first_req_dict = d
                    yield msg
            else:
                msg = dict_to_msg(request_dict)
                first_req = msg
                first_req_dict = request_dict
                yield msg

        def bidir_gen():
            start_dt = datetime.datetime.now()
            start_t = time.perf_counter()
            first_resp = None
            first_resp_dict = None

            try:
                for resp in method(req_gen(), metadata=grpc_metadata):
                    parsed = msg_to_dict(resp)
                    if first_resp is None:
                        first_resp = resp
                        first_resp_dict = parsed
                    yield parsed
            finally:
                end_t = time.perf_counter()
                end_dt = datetime.datetime.now()
                _trigger_details(
                    start_t,
                    end_t,
                    start_dt,
                    end_dt,
                    first_req,
                    first_resp,
                    first_req_dict,
                    first_resp_dict,
                )
                cleanup()

        return bidir_gen()

    else:
        cleanup()
        raise RuntimeError(f"Unhandled mode: {mode}")
