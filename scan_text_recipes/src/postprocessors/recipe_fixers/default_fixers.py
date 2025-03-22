import copy
from inspect import isabstract
from typing import Dict, List

import dictdiffer

from scan_text_recipes.src import RECIPE_FIXERS_PACKAGE_PATH, MODEL_INTERFACE_PACKAGE_PATH, PROMPTS_PACKAGE_PATH
from scan_text_recipes.src.model_interface.remote_model_interface import ModelInterface, RemoteAPIModelInterface
from scan_text_recipes.src.postprocessors.post_processors import PostProcessor
from scan_text_recipes.src.prompt_organizers.base_prompts_container import BasePromptsContainer
from scan_text_recipes.src.prompt_organizers.fixer_prompt_container import DefaultRefinerPromptsContainer
from scan_text_recipes.src.postprocessors.recipe_fixers.validation_methods import ValidationMethod
from scan_text_recipes.src.unit_converters.units_extractor import UnitsHandler
from scan_text_recipes.tests.examples_for_tests import load_unstructured_text_test_recipe, load_structured_test_recipe, \
    load_test_architecture_config, load_test_setup_config
from scan_text_recipes.utils.file_utils import dynamic_import_from_packages
from scan_text_recipes.utils.utils import list_it, read_model_config, load_or_create_instance


class RemoveFakes(PostProcessor):
    def process_recipe(self, recipe_dict: Dict[str, List], recipe_text: str, **kwargs) -> [bool, Dict[str, List]]:
        recipe_dict_fixed = copy.deepcopy(recipe_dict)
        # remove fake keys (ingredients or rosources) from the recipe
        for key in recipe_dict[self.section_name]:
            if key.get("name") not in recipe_text:
                recipe_dict_fixed[self.section_name].remove(key)
                # remove edges of fake ingredients from the recipe
                for edge in recipe_dict["edges"]:
                    if edge.get("from") == key.get("name") or edge.get("to") == key.get("name"):
                        recipe_dict_fixed["edges"].remove(edge)
        return True, recipe_dict_fixed


class RemoveFakeIngredients(RemoveFakes):
    """
    Remove fake ingredients from the recipe.
    """
    def __init__(self, setup_config: Dict, **kwargs):
        super().__init__(setup_config, "ingredients", **kwargs)


class RemoveFakeResources(RemoveFakes):
    """
    Remove fake resources from the recipe.
    """
    def __init__(self, setup_config: Dict, **kwargs):
        super().__init__(setup_config, "resources", **kwargs)


class RecipeFixer(PostProcessor):
    """
    Base class for recipe fixers.
    """
    def __init__(self, config: Dict, section_name: str, model_interface: ModelInterface,  language: str,
                 refiner_prompts: BasePromptsContainer = None, setup_config: Dict = None, **kwargs):
        super().__init__(config, section_name, **kwargs)

        self.model_interface = load_or_create_instance(
            model_interface, ModelInterface, MODEL_INTERFACE_PACKAGE_PATH, **kwargs
        )
        refiner_prompts = DefaultRefinerPromptsContainer(setup_config, language=language) if refiner_prompts is None else refiner_prompts
        self.prompts = load_or_create_instance(
            refiner_prompts, BasePromptsContainer, PROMPTS_PACKAGE_PATH, **kwargs
        )
        self.units_interpreter = UnitsHandler()

        # load all validation methods
        self.validation_methods = dynamic_import_from_packages(
            [RECIPE_FIXERS_PACKAGE_PATH],
            lambda x: issubclass(x, ValidationMethod) and not isabstract(x)
        )

    def create_questions_user_prompt(self, recipe_dict: Dict[str, List], recipe_text: str) -> str:
        section = copy.deepcopy(recipe_dict[self.section_name])
        for field in self.config['FIELDS']:
            for field_name in field:
                for method in list_it(field[field_name]):
                    if method is None:
                        continue
                    for sec_idx, section_field in enumerate(section):
                        if field_name not in section_field:
                            section[sec_idx][field_name] = None
                        elif isinstance(section_field[field_name], str) and section_field[field_name].startswith("$$$"):
                            # Skip already marked fields
                            continue
                        value = self.units_interpreter.get_magnitude(section_field[field_name])
                        if not getattr(self.validation_methods[method], 'validate')(value):
                            section[sec_idx][field_name] = f"$$${getattr(self.validation_methods[method], 'refinement_instructions')()}$$$"


        return self.prompts.user_recipe_prompt(
            section_name=self.section_name,
            section=section,
            recipe_text=recipe_text,
        )

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


class IngredientRecipeFixer(RecipeFixer):
    """
    Recipe fixer for ingredients.
    """
    def __init__(self, config, *args, **kwargs):
        super().__init__(config, "ingredients", *args, **kwargs)


class ResourceRecipeFixer(RecipeFixer):
    """
    Recipe fixer for resources.
    """
    def __init__(self, config, *args, **kwargs):
        super().__init__(config, "resources", *args, **kwargs)


if __name__ == '__main__':
    # Load the model configuration
    model_config = read_model_config()
    interface = RemoteAPIModelInterface(config=model_config)

    # Load example prompts
    original_text = load_unstructured_text_test_recipe()
    initially_structured_recipe = load_structured_test_recipe()

    # load arhitecture config
    architecture_config = load_test_architecture_config()

    # test ingredient validator
    ingredients_validator = IngredientRecipeFixer(
        config=architecture_config['PROCESSING_PIPELINE']['POST_PROCESSORS'][2]['IngredientRecipeFixer'],
        model_interface=interface,
        setup_config=load_test_setup_config()

    )
    recipe_with_fixed_ingredients = ingredients_validator.process_recipe(initially_structured_recipe, original_text)
    print("Fixed ingredients:")
    diff = list(dictdiffer.diff(initially_structured_recipe, recipe_with_fixed_ingredients))
    for d in diff:
        print(d)

    # test resources validator
    resources_validator = ResourceRecipeFixer(
        config=architecture_config['PROCESSING_PIPELINE']['POST_PROCESSORS'][3]['ResourceRecipeFixer'],
        model_interface=interface,
        setup_config=load_test_setup_config()
    )

    recipe_with_fixed_resources = resources_validator.process_recipe(initially_structured_recipe, original_text)
    print("Fixed resources:")
    diff = list(dictdiffer.diff(initially_structured_recipe, recipe_with_fixed_resources))
    for d in diff:
        print(d)
