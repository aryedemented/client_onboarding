from typing import Dict, List

from scan_text_recipes.src.loop_container import LoopContainer
from scan_text_recipes.src.model_interface.remote_model_interface import ModelInterface, RemoteAPIModelInterface
from scan_text_recipes.src.prompt_organizers.base_prompts_container import BasePromptsContainer
from scan_text_recipes.src.prompt_organizers.simplifier_prompts_container import SimplifierPromptsContainer
from scan_text_recipes.tests.examples_for_tests import load_complex_text_test_recipe


class PreProcessor:
    """
    Base class for all preprocessors.
    """
    def __init__(self, config: Dict, language: str):
        self.config = config
        self.language = language


class PreProcessorsLoopContainer(LoopContainer, PreProcessor):
    def __init__(self, iterations: int, segment_config: List[Dict], **kwargs):
        LoopContainer.__init__(
            self,
            iterations,
            package_path="scan_text_recipes.src.preprocessors",
            segment_config=segment_config,
            class_type=PreProcessor,
            **kwargs
        )
        PreProcessor.__init__(self, config={}, language="")

    def process_recipe(self, recipe_text: str) -> [bool, str]:
        # TODO: Implement the logic to run each segment of the pipeline
        ...


class TextCleaner(PreProcessor):
    """
    Clean Text - language nuances etc (TBD).
    """
    def __init__(self, config: Dict = None, language: str = None):
        super().__init__(config, language=language)

    def process_recipe(self, recipe_text: str) -> [bool, str]:
        """
        Process the recipe text.
        """
        return True, recipe_text


class TextSimplifier(PreProcessor):
    """
    Simplifies_text if too long.
    """
    def __init__(
            self,
            max_tokens: int,
            language: str,
            model_interface: ModelInterface = None,
            prompts: BasePromptsContainer = None,
            config: Dict = None
    ):
        super().__init__(config, language=language)
        self.config = config
        self.max_tokens = max_tokens
        self.model_interface = model_interface
        self.prompts = prompts if prompts else SimplifierPromptsContainer(self.config, self.language)

    def process_recipe(self, recipe_text: str) -> [bool, str]:
        """
        Simplify the recipe text.
        """
        if self.model_interface.get_number_of_tokens_from_the_text(recipe_text) > self.max_tokens:
            # Simplify the text using the model interface
            simple_text = self.model_interface.get_text_answer(
                messages=[
                    {"role": "system", "content": self.prompts.system_prompt()},
                    {"role": "user", "content": self.prompts.user_recipe_prompt(recipe_text)},
                    {"role": "assistant", "content": self.prompts.assistant_prompt()}
                ]
            )
            return True, simple_text
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
