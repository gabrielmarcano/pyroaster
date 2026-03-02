import time

LEVELS = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}


class SimpleLogger:
    def __init__(self, level="INFO"):
        self.__level = LEVELS.get(level, 1)

    def log(self, message, level="INFO"):
        if LEVELS.get(level, 1) < self.__level:
            return
        t = time.localtime()
        print(f"[{t[3]:02d}:{t[4]:02d}:{t[5]:02d}] [{level}] {message}")

    def warning(self, message):
        self.log(message, "WARNING")

    def info(self, message):
        self.log(message, "INFO")

    def error(self, message):
        self.log(message, "ERROR")

    def debug(self, message):
        self.log(message, "DEBUG")
