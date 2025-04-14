import os
from abc import abstractmethod


class BaseLogger:
    def __init__(self, name: str, **kwargs):
        self.name = name
        self.client_name = os.getenv("CLIENT_NAME")
        self.dish_name = os.getenv("DISH_NAME")

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


class DummyLogger(BaseLogger):
    def __init__(self, **kwargs):
        kwargs["name"] = "DummyLogger"
        super().__init__(**kwargs)

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
        print(f"[{self.client_name}/{self.dish_name}]{self.name}: {message}")

    def info(self, message: str):
        print(f"[{self.client_name}/{self.dish_name}]{self.name} [INFO]: {message}")

    def warning(self, message: str):
        print(f"[{self.client_name}/{self.dish_name}]{self.name} [WARNING]: {message}")

    def error(self, message: str):
        print(f"[{self.client_name}/{self.dish_name}]{self.name} [ERROR]: {message}")

    def critical(self, message: str):
        print(f"[{self.client_name}/{self.dish_name}]{self.name} [CRITICAL]: {message}")
