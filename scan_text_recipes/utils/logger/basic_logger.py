from abc import abstractmethod


class BaseLogger:
    def __init__(self, name: str, **kwargs):
        self.name = name

    @abstractmethod
    def log(self, message: str):
        ...

    @abstractmethod
    def info(self, message: str):
        ...

    @abstractmethod
    def warning(self, message: str):
        ...

    @abstractmethod
    def error(self, message: str):
        ...

    @abstractmethod
    def critical(self, message: str):
        ...


class DummyLogger:
    def log(self, message: str):
        ...

    def info(self, message: str):
        ...

    def warning(self, message: str):
        ...

    def error(self, message: str):
        ...

    def critical(self, message: str):
        ...


class Logger(BaseLogger):
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
