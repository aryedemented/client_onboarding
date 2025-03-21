from abc import abstractmethod
from typing import Dict


class BasePromptsContainer:
    def __init__(self, config: Dict, language: str, force_ingredients: bool = False, force_resources: bool = False):
        self.config = config
        self.language = language
        self.force_ingredients = force_ingredients
        self.force_resources = force_resources

    @staticmethod
    @abstractmethod
    def system_prompt() -> str:
        ...

    @staticmethod
    @abstractmethod
    def user_recipe_prompt(recipe_text: str, **kwargs) -> str:
        ...

    @staticmethod
    @abstractmethod
    def assistant_prompt(**kwargs) -> str:
        ...
