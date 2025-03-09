import time


class SimpleLogger:
    def __init__(self):
        pass

    def log(self, message, level="INFO"):
        timestamp = time.localtime()
        print(f"[{timestamp[3]}:{timestamp[4]}:{timestamp[5]}] [{level}] {message}")

    def warning(self, message):
        self.log(message, "WARNING")

    def info(self, message):
        self.log(message, "INFO")

    def error(self, message):
        self.log(message, "ERROR")

    def debug(self, message):
        self.log(message, "DEBUG")
