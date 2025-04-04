import copy
from abc import abstractmethod
from typing import Dict, List

from scan_text_recipes.src.issues_class_format import SupplementaryPromptQuestion
from scan_text_recipes.src.postprocessors.recipe_fixers.default_fixers import RecipeFixer
from scan_text_recipes.tests.examples_for_tests import load_structured_test_recipe, load_unstructured_text_test_recipe, \
    load_test_setup_config
from scan_text_recipes.utils.logger.basic_logger import Logger
from scan_text_recipes.utils.utils import list_it, read_yaml


class SupplementaryRecipeFixer(RecipeFixer):
    """
    Base class for recipe fixers.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, section_name=self.section_name, **kwargs)
        self.setup_config = kwargs.get("setup_config")
        self.setup_config = self.setup_config if isinstance(self.setup_config, dict) else read_yaml(self.setup_config)
        self.setup_units = self.setup_config[self.setup_section]

    @property
    @abstractmethod
    def setup_section(self):
        ...

    @property
    @abstractmethod
    def section_name(self):
        ...

    def find_issues(self, recipe_dict: Dict[str, List]) -> [str, List[SupplementaryPromptQuestion]]:
        section = copy.deepcopy(recipe_dict[self.section_name])
        issues = []
        for field in self.config['FIELDS']:
            for field_name in field:
                for method in list_it(field[field_name]):
                    if method is None:
                        continue
                    for sec_idx, section_field in enumerate(section):
                        value = None
                        if field_name in section_field and field_name in section[sec_idx]:
                            if 'intermediate' in section[sec_idx] and section[sec_idx]['intermediate']:
                                continue
                            else:
                                try:
                                    value = float(str(section_field[field_name]))
                                except ValueError:
                                    pass
                        if not getattr(self.validation_methods[method], 'validate')(value):
                            # check if units are valid (not suppose to be happening)
                            if section[sec_idx]['name'] not in self.setup_units or field_name not in self.setup_units[section[sec_idx]['name']].keys():
                                continue
                            question = SupplementaryPromptQuestion(
                                format=field_name,
                                section=section[sec_idx]['name'],
                                field_name=field_name,
                                section_index=sec_idx,
                                units=self.setup_units[section[sec_idx]['name']][field_name]
                            )

                            self.logger.warning(f': "{question.question}"')
                            issues.append(question)
        issues = list(filter(lambda x: x is not None, issues))
        return issues

    def create_questions_user_prompt(self, recipe_dict: Dict[str, List], recipe_text: str) -> [str, List[
            SupplementaryPromptQuestion]]:
        questions = self.find_issues(recipe_dict)

        answer = self.prompts.user_recipe_prompt(
            questions=questions,
            recipe_text=recipe_text,
        )
        return answer, questions

    def process_recipe(self, recipe_dict: Dict[str, List], recipe_text: str, **kwargs) -> [bool, Dict[str, List]]:
        """
        Refine the recipe.
        :param recipe_dict: Structured recipe.
        :param recipe_text: Original text.
        :return: Refined recipe.
        """
        user_prompts, questions = self.create_questions_user_prompt(recipe_dict, recipe_text)
        messages = [
            {"role": "system", "content": self.prompts.system_prompt()},
            {"role": "user", "content": user_prompts},
            {"role": "assistant", "content": self.prompts.assistant_prompt()}
        ]
        res, answers = self.model_interface.get_structured_answer(messages=messages)
        recipe_dict = self.create_updated_recipe_dict(answers, questions, recipe_dict)
        return res, recipe_dict

    def create_updated_recipe_dict(self, answers: List[Dict], questions: List[SupplementaryPromptQuestion], recipe_dict: Dict[str, List]) -> Dict[str, List]:
        """
        Update the original recipe dictionary with the refined section.
        :param questions: question classes, holding field names and indices to be updated.
        :param answers: answers from model.
        :param recipe_dict: Original recipe dictionary.
        """
        for question, answer in zip(questions, answers):
            try:
                recipe_dict[self.section_name][question.section_index][question.field_name] = float(
                    answer['value'])
            except ValueError:
                recipe_dict[self.section_name][question.section_index][question.field_name] = answer['value']
        return recipe_dict


class IngredientsSupplementaryFixer(SupplementaryRecipeFixer):
    setup_section = "ALLOWED_INGREDIENTS"
    section_name: str = "ingredients"


class ResourcesSupplementaryFixer(SupplementaryRecipeFixer):
    setup_section = "ALLOWED_RESOURCES"
    section_name: str = "resources"


def ingredients_fixer_test():
    setup_config = load_test_setup_config()
    client_config = dict(FIELDS=[
        dict(quantity=["NotNull", "TypeFloat"]),
    ])

    recipe_fixer = IngredientsSupplementaryFixer(
        refiner_prompts='SupplementaryRefinerPromptsContainer',
        units_interpreter=None,
        validation_methods=None,
        logger=Logger(name="RecipeFixer"),
        config=client_config,
        **{"model_interface": "RemoteAPIModelInterface", "language": "Hebrew", "setup_config": setup_config, "force_ingredients": True, "force_resources": True}
    )
    recipe_dict = load_structured_test_recipe()
    recipe_text = load_unstructured_text_test_recipe()
    result = recipe_fixer.process_recipe(recipe_dict, recipe_text)
    print(result)


def resources_fixer_test():
    setup_config = load_test_setup_config()
    client_config = dict(FIELDS=[
        dict(temperature=["NotNull", "TypeFloat"], usage_time=["NotNull", "TypeFloat"]),
    ])

    recipe_fixer = ResourcesSupplementaryFixer(
        refiner_prompts='SupplementaryRefinerPromptsContainer',
        units_interpreter=None,
        validation_methods=None,
        logger=Logger(name="RecipeFixer"),
        config=client_config,
        **{"model_interface": "RemoteAPIModelInterface", "language": "Hebrew", "setup_config": setup_config, "force_ingredients": True, "force_resources": True}
    )
    recipe_dict = load_structured_test_recipe()
    recipe_text = load_unstructured_text_test_recipe()
    result = recipe_fixer.process_recipe(recipe_dict, recipe_text)
    print(result)


if __name__ == '__main__':
    ingredients_fixer_test()
    # resources_fixer_test()
