import os
from abc import abstractmethod
from typing import List, Dict

from scan_text_recipes import PROJECT_ROOT
from scan_text_recipes.src import MODEL_INTERFACE_PACKAGE_PATH, PROMPTS_PACKAGE_PATH, LOGGER_PACKAGE_PATH
from scan_text_recipes.src.model_interface.remote_model_interface import ModelInterface, RemoteAPIModelInterface
from scan_text_recipes.src.prompt_organizers.base_prompts_container import BasePromptsContainer
from scan_text_recipes.src.prompt_organizers.default_prompt_container import DefaultPromptsContainer
from scan_text_recipes.utils.logger.basic_logger import BaseLogger
from scan_text_recipes.utils.utils import load_or_create_instance
from scan_text_recipes.utils.visualize_recipe import create_recipe_graph
from scan_text_recipes.tests.examples_for_tests import load_test_setup_config, load_unstructured_text_test_recipe


class BaseMainProcessor:
    def __init__(self, logger=None, **kwargs):
        """
        Base class for main processors.
        :param logger: Logger instance for logging.
        """
        self.logger = load_or_create_instance(
            logger, BaseLogger, LOGGER_PACKAGE_PATH, **{**{"name": self.__class__.__name__}, **kwargs}
        )

    @abstractmethod
    def process_recipe(self, recipe: str) ->[bool, Dict]:
        """
        Format the recipe into a structured dictionary format.
        :param recipe: The recipe text to be formatted.
        :return: The formatted recipe as a dictionary.
        """
        raise NotImplementedError("Subclasses should implement this method.")


class DefaultMainProcessor(BaseMainProcessor):
    """
    Complete formatter for the recipe
    """
    def __init__(self, model_interface: ModelInterface, prompts: BasePromptsContainer = None, **kwargs):
        """
        This class performs initial transformation of recipe fro  text to structured dictionary format
        :param model_interface:
        :param prompts:
        """

        super().__init__(**kwargs)
        self.model_interface = load_or_create_instance(
            model_interface, ModelInterface, MODEL_INTERFACE_PACKAGE_PATH, **kwargs
        )
        self.prompts = load_or_create_instance(
            prompts, BasePromptsContainer, PROMPTS_PACKAGE_PATH, **kwargs
        )

    def query_default_formatter_message(self, recipe) -> List[Dict]:
        """
        Constructs message for structuring the recipe
        :param recipe:
        :return:
        """
        return [
            {"role": "system", "content": "You are a helpful assistant that extracts and structures recipes."},
            {"role": "user", "content": f"Format the following recipe into JSON:\n{self.prompts.user_recipe_prompt(recipe)}"},
            {"role": "assistant", "content": self.prompts.assistant_prompt()},
        ]

    def process_recipe(self, recipe_text: str) -> [bool, Dict]:
        self.logger.log("Processing recipe...")
        messages = self.query_default_formatter_message(recipe_text)
        res, formatter_recipe = self.model_interface.get_structured_answer(messages=messages)
        if res:
            self.logger.log("Recipe processed successfully.")
        else:
            self.logger.log("Error processing recipe.")
        return res, formatter_recipe


if __name__ == '__main__':
    formatter = DefaultMainProcessor(
        model_interface=RemoteAPIModelInterface(),
        prompts=DefaultPromptsContainer(config=load_test_setup_config(), language="English", force_ingredients=True, force_resources=True)
    )
    raw_recipe_text = load_unstructured_text_test_recipe()
    structured_recipe = formatter.process_recipe(raw_recipe_text)
    print(f"Raw recipe text:\n{raw_recipe_text}")
    print(f"Structured recipe:\n{structured_recipe}")
    graph = create_recipe_graph(structured_recipe)
    graph.render(os.path.join(PROJECT_ROOT, "..", "structured_recipes", "tmp"), view=True)  # Saves and opens the graph
