import string

from utils.config_manager import Config, ConfigManager


class AppContext:
    def __init__(self):
        self.config_manager = None
        self.config: Config
        self.current_rpc: dict
        self.request_schema: dict
        self.data: dict
        self.log_buffer: str

    def init(self):
        self.current_rpc = {}
        self.request_schema = {}
        self.data = {}
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get()
        self.log_buffer = ""
