import copy
from typing import Dict, List, Union

from scan_text_recipes.src import PROMPTS_PACKAGE_PATH, MODEL_INTERFACE_PACKAGE_PATH, PRE_PROCESSORS_PACKAGE_PATH, \
    LOGGER_PACKAGE_PATH
from scan_text_recipes.src.loop_container import LoopContainer
from scan_text_recipes.src.model_interface.remote_model_interface import ModelInterface, RemoteAPIModelInterface
from scan_text_recipes.src.prompt_organizers.base_prompts_container import BasePromptsContainer
from scan_text_recipes.tests.examples_for_tests import load_complex_text_test_recipe
from scan_text_recipes.utils.logger.basic_logger import BaseLogger
from scan_text_recipes.utils.utils import load_or_create_instance


class PreProcessor:
    """
    Base class for all preprocessors.
    """
    def __init__(self, config: Dict, language: str, logger=None, **kwargs):
        self.config = config
        self.language = language
        self.logger = load_or_create_instance(
            logger, BaseLogger, LOGGER_PACKAGE_PATH, **{**{"name": self.__class__.__name__}, **kwargs}
        )


class PreProcessorsLoopContainer(LoopContainer, PreProcessor):
    def __init__(self, iterations: int, segment_config: List[Dict], **kwargs):
        PreProcessor.__init__(self, config={}, language="", **kwargs)
        LoopContainer.__init__(
            self,
            iterations,
            package_path=PRE_PROCESSORS_PACKAGE_PATH,
            segment_config=segment_config,
            class_type=PreProcessor,
            logger=self.logger,
            **{key: val for key, val in kwargs.items() if key != "logger"}
        )

    def _copy_tmp_recipe(self, **kwargs) -> str:
        return copy.deepcopy(kwargs.get("recipe_text"))

    def _run_loop(self, *args, **kwargs) -> [bool, str]:
        recipe_text: str = kwargs.get("recipe_text")
        for processor in self.processors:
            res, recipe_text = processor.process_recipe(recipe_text)
            if not res:
                self.logger.log(f"Error in {processor.__class__.__name__}")
                return False, recipe_text
        return True, recipe_text


class TextCleaner(PreProcessor):
    """
    Clean Text - language nuances etc (TBD).
    """
    def __init__(self, config: Dict = None, language: str = None, **kwargs):
        super().__init__(config, language=language, **kwargs)

    def process_recipe(self, recipe_text: str) -> [bool, str]:
        """
        Process the recipe text.
        """
        self.logger.log("Cleaning the recipe text...")
        ...
        self.logger.log("Cleaning the recipe text completed")
        return True, recipe_text


class TextSimplifier(PreProcessor):
    """
    Simplifies_text if too long.
    """
    def __init__(
            self,
            max_tokens: int,
            language: str,
            model_interface: Union[ModelInterface, str, Dict] = None,
            prompts: BasePromptsContainer = None,
            config: Dict = None,
            **kwargs
    ):
        super().__init__(config, language=language, **kwargs)
        self.config = config
        self.max_tokens = max_tokens
        self.model_interface = load_or_create_instance(
            model_interface, ModelInterface, MODEL_INTERFACE_PACKAGE_PATH, **kwargs
        )
        self.prompts = load_or_create_instance(
            prompts, BasePromptsContainer, PROMPTS_PACKAGE_PATH, **kwargs
        )

    def process_recipe(self, recipe_text: str) -> [bool, str]:
        """
        Simplify the recipe text.
        """
        if self.model_interface.get_number_of_tokens_from_the_text(recipe_text) > self.max_tokens:
            self.logger.log(f"Recipe text is too long ({self.max_tokens} tokens), simplifying...")
            # Simplify the text using the model interface
            simple_text = self.model_interface.get_text_answer(
                messages=[
                    {"role": "system", "content": self.prompts.system_prompt()},
                    {"role": "user", "content": self.prompts.user_recipe_prompt(recipe_text)},
                    {"role": "assistant", "content": self.prompts.assistant_prompt()}
                ]
            )
            return True, simple_text
        else:
            self.logger.log(f"Recipe text is within the limit ({self.max_tokens} tokens), no simplification needed.")
            # No simplification needed, return the original text
        return True, recipe_text


if __name__ == '__main__':
    # Example usage
    text_cleaner = TextCleaner(config={})
    text_simplifier = TextSimplifier(max_tokens=1000, language="English", model_interface=RemoteAPIModelInterface())

    loaded_recipe_text = load_complex_text_test_recipe()
    _, cleaned_text = text_cleaner.process_recipe(loaded_recipe_text)
    _, simplified_text = text_simplifier.process_recipe(cleaned_text)

    print("Cleaned Text:", cleaned_text)
    print("Simplified Text:", simplified_text)
