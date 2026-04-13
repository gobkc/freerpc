import importlib
import json
import os
import shutil
import sys
import tempfile
from typing import Any, Dict, Generator, Iterable, Optional, Union

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

    if mode == "unary":
        try:
            req = dict_to_msg(request_dict)
            resp = method(req, metadata=grpc_metadata)
            return msg_to_dict(resp)
        finally:
            cleanup()
    elif mode == "server_streaming":
        req = dict_to_msg(request_dict)

        def server_gen():
            try:
                for resp in method(req, metadata=grpc_metadata):
                    yield msg_to_dict(resp)
            finally:
                cleanup()

        return server_gen()
    elif mode == "client_streaming":

        def req_gen():
            if request_stream is not None:
                for d in request_stream:
                    yield dict_to_msg(d)
            else:
                yield dict_to_msg(request_dict)

        try:
            resp = method(req_gen(), metadata=grpc_metadata)
            return msg_to_dict(resp)
        finally:
            cleanup()
    elif mode == "bidirectional":

        def req_gen():
            if request_stream is not None:
                for d in request_stream:
                    yield dict_to_msg(d)
            else:
                yield dict_to_msg(request_dict)

        def bidir_gen():
            try:
                for resp in method(req_gen(), metadata=grpc_metadata):
                    yield msg_to_dict(resp)
            finally:
                cleanup()

        return bidir_gen()
    else:
        cleanup()
        raise RuntimeError(f"Unhandled mode: {mode}")
