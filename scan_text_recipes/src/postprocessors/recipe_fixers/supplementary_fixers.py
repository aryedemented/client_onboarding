import copy
from abc import abstractmethod
from typing import Dict, List
from dataclasses import dataclass

from scan_text_recipes.src.postprocessors.recipe_fixers.default_fixers import RecipeFixer
from scan_text_recipes.tests.examples_for_tests import load_structured_test_recipe, load_unstructured_text_test_recipe, \
    load_test_setup_config
from scan_text_recipes.utils.logger.basic_logger import Logger
from scan_text_recipes.utils.utils import list_it


@dataclass
class SupplementaryPromptQuestion:
    format: str
    section: str
    field_name: str
    section_index: int
    units: str

    @property
    def question(self) -> str:
        return f'What is the {self.field_name} for {self.section} in the recipe in "{self.units}" units?'

    @property
    def format_text(self) -> str:
        return f'{{ {self.section}: "numeric value" , units: "{self.units}"}}'


class SupplementaryRecipeFixer(RecipeFixer):
    """
    Base class for recipe fixers.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_config = kwargs.get("setup_config")
        self.setup_units = self.setup_config[self.setup_section]

    @property
    @abstractmethod
    def setup_section(self):
        ...

    @property
    @abstractmethod
    def section_name(self):
        ...

    def create_questions_user_prompt(self, recipe_dict: Dict[str, List], recipe_text: str) -> str:
        section = copy.deepcopy(recipe_dict[self.section_name])
        questions = []
        for field in self.config['FIELDS']:
            for field_name in field:
                for method in list_it(field[field_name]):
                    if method is None:
                        continue
                    for sec_idx, section_field in enumerate(section):
                        if field_name not in section_field:
                            section[sec_idx][field_name] = None
                        value = self.units_interpreter.get_magnitude(str(section_field[field_name]))
                        if not getattr(self.validation_methods[method], 'validate')(value):
                            question = SupplementaryPromptQuestion(
                                format=field_name,
                                section=section[sec_idx]['name'],
                                field_name=field_name,
                                section_index=sec_idx,
                                units=self.setup_units[section[sec_idx]['name']]
                            )

                            self.logger.warning(f': "{question.question}"')
                            questions.append(question)

        answer = self.prompts.user_recipe_prompt(
            questions=questions,
            recipe_text=recipe_text,
        )
        return answer

    def process_recipe(self, recipe_dict: Dict[str, List], recipe_text: str, **kwargs) -> [bool, Dict[str, List]]:
        """
        Refine the recipe.
        :param recipe_dict: Structured recipe.
        :param recipe_text: Original text.
        :return: Refined recipe.
        """
        messages = [
            {"role": "system", "content": self.prompts.system_prompt()},
            {"role": "user", "content": self.create_questions_user_prompt(recipe_dict, recipe_text)},
            {"role": "assistant", "content": self.prompts.assistant_prompt()}
        ]
        res, refined_section = self.model_interface.get_structured_answer(messages=messages)
        refined_recipe = copy.deepcopy(recipe_dict)
        refined_recipe[self.section_name] = refined_section
        return res, refined_recipe


class IngredientsSupplementaryFixer(SupplementaryRecipeFixer):
    setup_section = "ALLOWED_INGREDIENTS"
    section_name: str = "ingredients"


class ResourcesSupplementaryFixer(SupplementaryRecipeFixer):
    setup_section = "ALLOWED_INGREDIENTS"
    section_name: str = "ingredients"


if __name__ == '__main__':
    from scan_text_recipes.src.model_interface.remote_model_interface import ModelInterface

    setup_config = load_test_setup_config()
    client_name = "italiano"
    client_config = dict(FIELDS=[
        dict(quantity=["NotNull", "TypeFloat"]),
    ])

    recipe_fixer = IngredientsSupplementaryFixer(
        section_name="ingredients",
        refiner_prompts='SupplementaryRefinerPromptsContainer',
        units_interpreter=None,
        validation_methods=None,
        logger=Logger(name="RecipeFixer"),
        config=client_config,
        model_interface=ModelInterface(),
        **{"language": "Hebrew", "setup_config": setup_config, "force_ingredients": True, "force_resources": True}
    )
    recipe_dict = load_structured_test_recipe()
    recipe_text = load_unstructured_text_test_recipe()
    result = recipe_fixer.process_recipe(recipe_dict, recipe_text)
    print(result)
