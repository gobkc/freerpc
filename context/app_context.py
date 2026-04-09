from utils.config_manager import Config, ConfigManager


class AppContext:
    def __init__(self):
        self.config_manager = None
        self.config: Config

    def init(self):

        self.config_manager = ConfigManager()
        self.config = self.config_manager.get()
