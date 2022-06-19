from pathlib import Path

class Config():
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.data_dir = self.base_dir/'data'
        self.log_dir = self.base_dir/'logs'