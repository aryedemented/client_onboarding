class Logger:
    def __init__(self, name: str):
        self.name = name

    def log(self, message: str):
        print(f"{self.name}: {message}")

    def info(self, message: str):
        print(f"{self.name} [INFO]: {message}")

    def warning(self, message: str):
        print(f"{self.name} [WARNING]: {message}")

    def error(self, message: str):
        print(f"{self.name} [ERROR]: {message}")

    def critical(self, message: str):
        print(f"{self.name} [CRITICAL]: {message}")
