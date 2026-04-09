import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class ProtoService:
    # 基础类型到 JSON Schema 的映射
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
        # 首先提取所有 message / enum 定义，用于生成 schema
        messages = ProtoService._parse_all_messages(content)

        services = []
        # 匹配 service 块
        service_blocks = re.findall(r"service\s+(\w+)\s*\{([\s\S]*?)\}", content)

        for service_name, body in service_blocks:
            rpcs = ProtoService._parse_rpcs(body, messages)

            services.append(
                {
                    "name": service_name,
                    "tabs": [
                        {
                            "request": {},
                            "metadata": {},
                            "response": {},
                            "log": {},
                        }
                    ],
                    "rpc": rpcs,
                }
            )

        return services

    @staticmethod
    def _parse_rpcs(content: str, messages: Dict[str, Any]) -> list:
        rpcs = []
        # 匹配 rpc，支持可选的 stream 关键字
        pattern = re.compile(
            r"rpc\s+(\w+)\s*\(\s*(stream\s+)?(\w+)\s*\)\s+returns\s*\(\s*(stream\s+)?(\w+)\s*\)"
        )
        matches = pattern.findall(content)

        for func, req_stream, req_type, resp_stream, resp_type in matches:
            # 确定 RPC 类型
            if req_stream and resp_stream:
                rpc_type = "bidirectional streaming"
            elif req_stream:
                rpc_type = "client streaming"
            elif resp_stream:
                rpc_type = "server streaming"
            else:
                rpc_type = "unary"

            # 生成请求与响应的 schema
            req_schema = ProtoService._get_message_schema(req_type, messages)
            resp_schema = ProtoService._get_message_schema(resp_type, messages)

            rpcs.append(
                {
                    "type": rpc_type,
                    "func": func,
                    "request": req_type,
                    "response": resp_type,
                    "request_schema": req_schema,
                    "response_schema": resp_schema,
                }
            )

        return rpcs

    @staticmethod
    def _parse_all_messages(content: str) -> Dict[str, Any]:
        """提取所有 message 和 enum 的定义，返回名称到结构字典的映射"""
        definitions = {}

        # 去除 // 和 /* */ 注释，避免干扰解析
        content = re.sub(r"//.*?$", "", content, flags=re.MULTILINE)
        content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)

        # 递归提取所有 message 和 enum 块
        # 简单方法：使用栈匹配大括号
        def extract_blocks(text: str, keyword: str):
            blocks = {}
            pattern = re.compile(rf"{keyword}\s+(\w+)\s*\{{")
            for match in pattern.finditer(text):
                name = match.group(1)
                start = match.end() - 1  # 指向开括号 '{'
                # 从 start 开始找到匹配的闭括号
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

        # 先处理枚举，因为消息字段可能引用它们
        for name, body in enum_bodies.items():
            definitions[name] = ProtoService._parse_enum_body(body)

        # 处理消息，此时枚举已就绪
        for name, body in message_bodies.items():
            definitions[name] = ProtoService._parse_message_body(body, definitions)

        return definitions

    @staticmethod
    def _parse_enum_body(body: str) -> Dict[str, Any]:
        """解析枚举内容，返回类似 {"type": "string", "enum": [...]} 的 schema"""
        values = []
        # 匹配枚举值定义，忽略选项
        for match in re.finditer(r"(\w+)\s*=\s*(\d+)\s*;", body):
            values.append(match.group(1))
        return {"type": "string", "enum": values}

    @staticmethod
    def _parse_message_body(body: str, definitions: Dict[str, Any]) -> Dict[str, Any]:
        """解析消息体，返回 JSON Schema 对象"""
        properties = {}
        required = []

        # 匹配字段定义：支持 [repeated] type name = number;
        # 同时处理 map<k, v> 语法
        field_pattern = re.compile(
            r"(repeated\s+)?(\w+(?:\.\w+)*|map<\s*\w+\s*,\s*\w+\s*>)\s+(\w+)\s*=\s*(\d+)\s*;"
        )
        for match in field_pattern.finditer(body):
            repeated = match.group(1) is not None
            type_str = match.group(2)
            field_name = match.group(3)
            # field_number = match.group(4)  # 暂不使用

            field_schema = None
            is_map = False
            map_key_type = None
            map_value_type = None

            map_match = re.match(r"map<\s*(\w+)\s*,\s*(\w+)\s*>", type_str)
            if map_match:
                is_map = True
                map_key_type = map_match.group(1)
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
                # oneof 字段一般不加 required
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
