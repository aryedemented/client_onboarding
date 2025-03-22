from abc import abstractmethod
from typing import Dict, Union

from scan_text_recipes.utils.utils import read_yaml


class BasePromptsContainer:
    def __init__(self, setup_config: Union[str, Dict], language: str, force_ingredients: bool = False, force_resources: bool = False, **kwargs):
        self.setup_config = setup_config if isinstance(setup_config, dict) else read_yaml(setup_config)
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
