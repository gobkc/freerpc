import re
from pathlib import Path
from typing import Any, Dict


class ProtoService:
    TYPE_MAPPING = {
        "double": {"type": "number", "format": "double"},
        "float": {"type": "number", "format": "float"},
        "int32": {"type": "integer", "format": "int32"},
        "int64": {"type": "integer", "format": "int64"},
        "uint32": {"type": "integer", "format": "uint32"},
        "uint64": {"type": "integer", "format": "uint64"},
        "sint32": {"type": "integer", "format": "sint32"},
        "sint64": {"type": "integer", "format": "sint64"},
        "fixed32": {"type": "integer", "format": "fixed32"},
        "fixed64": {"type": "integer", "format": "fixed64"},
        "sfixed32": {"type": "integer", "format": "sfixed32"},
        "sfixed64": {"type": "integer", "format": "sfixed64"},
        "bool": {"type": "boolean"},
        "string": {"type": "string"},
        "bytes": {"type": "string", "contentEncoding": "base64"},
    }

    @staticmethod
    def parse_proto_file(path: str) -> dict:
        content = Path(path).read_text(encoding="utf-8")
        package = ProtoService._parse_package(content)
        services = ProtoService._parse_services(content)
        return {
            "path": path,
            "package": package,
            "services": services,
        }

    @staticmethod
    def _parse_package(content: str) -> str:
        m = re.search(r"package\s+([\w\.]+);", content)
        return m.group(1) if m else ""

    @staticmethod
    def _parse_services(content: str) -> list:
        messages = ProtoService._parse_all_messages(content)
        services = []
        service_blocks = re.findall(r"service\s+(\w+)\s*\{([\s\S]*?)\}", content)

        for service_name, body in service_blocks:
            rpcs = ProtoService._parse_rpcs(body, messages)
            services.append(
                {
                    "name": service_name,
                    "rpc": rpcs,
                }
            )
        return services

    @staticmethod
    def _parse_rpcs(content: str, messages: Dict[str, Any]) -> list:
        rpcs = []
        pattern = re.compile(
            r"rpc\s+(\w+)\s*\(\s*(stream\s+)?(\w+)\s*\)\s+returns\s*\(\s*(stream\s+)?(\w+)\s*\)"
        )
        matches = pattern.findall(content)

        for func, req_stream, req_type, resp_stream, resp_type in matches:
            if req_stream and resp_stream:
                rpc_type = "bidirectional streaming"
            elif req_stream:
                rpc_type = "client streaming"
            elif resp_stream:
                rpc_type = "server streaming"
            else:
                rpc_type = "unary"

            req_schema = ProtoService._get_message_schema(req_type, messages)
            resp_schema = ProtoService._get_message_schema(resp_type, messages)

            rpcs.append(
                {
                    "host": "",
                    "type": rpc_type,
                    "func": func,
                    "request": req_type,
                    "response": resp_type,
                    "request_schema": req_schema,
                    "response_schema": resp_schema,
                    "metadata_schema": {
                        "type": "object",
                        "additionalProperties": {"type": "string"},
                    },
                    "parameters": "{}",
                    "metadata": "{}",
                    "result": "",
                    "log": "",
                }
            )
        return rpcs

    @staticmethod
    def _parse_all_messages(content: str) -> Dict[str, Any]:
        definitions = {}
        content = re.sub(r"//.*?$", "", content, flags=re.MULTILINE)
        content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)

        def extract_blocks(text: str, keyword: str):
            blocks = {}
            pattern = re.compile(rf"{keyword}\s+(\w+)\s*\{{")
            for match in pattern.finditer(text):
                name = match.group(1)
                start = match.end() - 1
                balance = 0
                end = start
                for i, ch in enumerate(text[start:], start):
                    if ch == "{":
                        balance += 1
                    elif ch == "}":
                        balance -= 1
                        if balance == 0:
                            end = i
                            break
                body = text[start + 1 : end]
                blocks[name] = body
            return blocks

        message_bodies = extract_blocks(content, "message")
        enum_bodies = extract_blocks(content, "enum")

        for name, body in enum_bodies.items():
            definitions[name] = ProtoService._parse_enum_body(body)

        for name, body in message_bodies.items():
            definitions[name] = ProtoService._parse_message_body(body, definitions)

        return definitions

    @staticmethod
    def _parse_enum_body(body: str) -> Dict[str, Any]:
        values = []
        for match in re.finditer(r"(\w+)\s*=\s*(\d+)\s*;", body):
            values.append(match.group(1))
        return {"type": "string", "enum": values}

    @staticmethod
    def _parse_message_body(body: str, definitions: Dict[str, Any]) -> Dict[str, Any]:
        properties = {}
        required = []

        field_pattern = re.compile(
            r"(repeated\s+)?(\w+(?:\.\w+)*|map<\s*\w+\s*,\s*\w+\s*>)\s+(\w+)\s*=\s*(\d+)\s*;"
        )
        for match in field_pattern.finditer(body):
            repeated = match.group(1) is not None
            type_str = match.group(2)
            field_name = match.group(3)

            field_schema = None
            is_map = False
            # map_key_type = None
            map_value_type = ""

            map_match = re.match(r"map<\s*(\w+)\s*,\s*(\w+)\s*>", type_str)
            if map_match:
                is_map = True
                # map_key_type = map_match.group(1)
                map_value_type = map_match.group(2)

            if is_map:
                value_schema = ProtoService._type_to_schema(map_value_type, definitions)
                field_schema = {"type": "object", "additionalProperties": value_schema}
            else:
                base_schema = ProtoService._type_to_schema(type_str, definitions)
                if repeated:
                    field_schema = {"type": "array", "items": base_schema}
                else:
                    field_schema = base_schema
                    if not repeated and type_str in ProtoService.TYPE_MAPPING:
                        required.append(field_name)

            properties[field_name] = field_schema

        oneof_pattern = re.compile(r"oneof\s+\w+\s*\{([^}]*)\}")
        for oneof_match in oneof_pattern.finditer(body):
            oneof_body = oneof_match.group(1)
            for field_match in re.finditer(
                r"(\w+(?:\.\w+)*)\s+(\w+)\s*=\s*(\d+)\s*;", oneof_body
            ):
                type_str = field_match.group(1)
                field_name = field_match.group(2)
                properties[field_name] = ProtoService._type_to_schema(
                    type_str, definitions
                )

        result = {"type": "object", "properties": properties}
        if required:
            result["required"] = required
        return result

    @staticmethod
    def _type_to_schema(type_str: str, definitions: Dict[str, Any]) -> Dict[str, Any]:
        clean_type = type_str.lstrip(".")
        if clean_type in ProtoService.TYPE_MAPPING:
            return ProtoService.TYPE_MAPPING[clean_type].copy()
        elif clean_type in definitions:
            return definitions[clean_type].copy()
        else:
            return {"type": "string"}

    @staticmethod
    def _get_message_schema(msg_name: str, messages: Dict[str, Any]) -> Dict[str, Any]:
        if msg_name in messages:
            return messages[msg_name]
        if msg_name in ProtoService.TYPE_MAPPING:
            return ProtoService.TYPE_MAPPING[msg_name].copy()
        return {}
