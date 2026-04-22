import json
from pathlib import Path
from typing import TypedDict, cast


class Rpc(TypedDict):
    host: str
    type: str
    func: str
    request: str
    response: str
    request_schema: dict
    response_schema: dict
    parameters: str
    metadata: str
    result: str
    log: str


class Service(TypedDict):
    name: str
    rpc: list[Rpc]


class Proto(TypedDict):
    path: str
    package: str
    services: list[Service]


class Config(TypedDict):
    host: str
    protos: list[Proto]


class ConfigManager:
    def __init__(self):
        self.base_dir = Path.home() / ".local" / "freerpc"
        self.config_path = self.base_dir / "config.json"
        self.config: Config

        self._ensure_dir()
        self._ensure_config()
        self._load_config()

    def _ensure_dir(self):
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _default_config(self) -> Config:
        return {
            "host": "",
            "protos": [
                {
                    "path": "",
                    "package": "",
                    "services": [
                        {
                            "name": "",
                            "rpc": [
                                {
                                    "host": "",
                                    "type": "",
                                    "func": "",
                                    "request": "",
                                    "response": "",
                                    "request_schema": {},
                                    "response_schema": {},
                                    "metadata": "",
                                    "parameters": "",
                                    "log": {},
                                }
                            ],
                        }
                    ],
                }
            ],
        }

    def _ensure_config(self):
        if not self.config_path.exists():
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._default_config(), f, ensure_ascii=False, indent=4)

    def _load_config(self):
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = cast(Config, json.load(f))

    def save(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)

    def set_config(self, config: Config):
        self.config = config
        self.save()

    def update_rpc_fields(
        self,
        package: str,
        service_name: str,
        func_name: str,
        updates: dict,
    ) -> Config:
        found = False
        for proto in self.config.get("protos", []):
            if proto.get("package") != package:
                continue
            for service in proto.get("services", []):
                if service.get("name") != service_name:
                    continue
                for rpc in service.get("rpc", []):
                    if rpc.get("func") == func_name:
                        for k, v in updates.items():
                            if k in rpc:
                                rpc[k] = v
                            else:
                                rpc[k] = v
                        found = True
                        break
        if not found:
            raise ValueError(
                f"RPC not found: package={package}, service={service_name}, func={func_name}"
            )
        self.save()
        return self.config

    def get(self) -> Config:
        return self.config

    def update(self, key, value):
        self.config[key] = value
        self.save()
