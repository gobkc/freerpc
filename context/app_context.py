from utils.config_manager import Config, ConfigManager


class AppContext:
    def __init__(self):
        self.config_manager = None
        self.config: Config
        self.current_rpc: dict
        self.request_schema: dict

    def init(self):
        self.current_rpc = {}
        self.request_schema = {}
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get()
