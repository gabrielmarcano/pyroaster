import utime


class SimpleLogger:
    def __init__(self):
        self.timestamp = utime.localtime()

    def log(self, message, level="INFO"):
        print(
            f"[{self.timestamp[3]}:{self.timestamp[4]}:{self.timestamp[5]}] [{level}] {message}"
        )

    def warning(self, message):
        self.log(message, "WARNING")

    def info(self, message):
        self.log(message, "INFO")

    def error(self, message):
        self.log(message, "ERROR")

    def debug(self, message):
        self.log(message, "DEBUG")
        self.log(message, "CRITICAL")
