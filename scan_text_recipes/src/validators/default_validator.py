import os
from abc import abstractmethod
from typing import Dict
import sys

# Add the repo root (parent of client_boarding) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from scan_text_recipes.utils.paths import PROJECT_ROOT
from scan_text_recipes.src import LOGGER_PACKAGE_PATH
from scan_text_recipes.src.postprocessors.graph_refinement import GraphRefinement
from scan_text_recipes.src.postprocessors.recipe_fixers.supplementary_fixers import IngredientsSupplementaryFixer, \
    ResourcesSupplementaryFixer
from scan_text_recipes.tests.examples_for_tests import load_structured_test_recipe, load_unstructured_text_test_recipe, \
    load_test_setup_config, load_test_architecture_config
from scan_text_recipes.utils.logger.basic_logger import BaseLogger, DummyLogger
from scan_text_recipes.utils.utils import load_or_create_instance, read_yaml


class BaseValidator:
    @abstractmethod
    def validate(self, recipe_dict: Dict, recipe_text: str):
        ...


class DefaultValidator(BaseValidator):
    def __init__(self, config: Dict, setup_config: Dict, logger=None, **kwargs):
        self.config = config
        self.logger = load_or_create_instance(
            logger, BaseLogger, LOGGER_PACKAGE_PATH, **{**{"name": self.__class__.__name__}, **kwargs}
        )

        self.graph_validator = GraphRefinement(
            model_interface=None,
            setup_config=setup_config,
            logger=DummyLogger(),
            **kwargs,
        )
        cfg = self.get_pot_proc_config(self.config, "IngredientsSupplementaryFixer")

        self.ingredients_validator = IngredientsSupplementaryFixer(
            config=cfg,
            model_interface=None,
            setup_config=setup_config,
            logger=DummyLogger(),
            **kwargs,
        )
        cfg = self.get_pot_proc_config(self.config, "ResourcesSupplementaryFixer")

        self.resources_validator = ResourcesSupplementaryFixer(
            config=cfg,
            model_interface=None,
            setup_config=setup_config,
            logger=DummyLogger(),
            **kwargs,
        )

    @staticmethod
    def get_pot_proc_config(config: Dict, post_processor_name: str):
        part_cfg = [key_val for key_val in config['PROCESSING_PIPELINE']['POST_PROCESSORS']
                    if list(key_val.keys())[0] == post_processor_name][0][post_processor_name]['config']
        return part_cfg

    def validate(self, recipe_dict: Dict, recipe_text: str):
        issues = self.graph_validator.find_issues(recipe_dict=recipe_dict, recipe_text=recipe_text)
        issues.extend(self.ingredients_validator.find_issues(recipe_dict=recipe_dict))
        issues.extend(self.resources_validator.find_issues(recipe_dict=recipe_dict))
        for issue in issues:
            self.logger.error(f"{issue.problem}")
        res = False if issues else True
        return res, issues


if __name__ == '__main__':
    # Example usage
    validator = DefaultValidator(
        config=load_test_architecture_config(),
        setup_config=load_test_setup_config(),
        language="Hebrew",
        logger="Logger",
    )
    # structured_recipe = load_structured_test_recipe()
    structured_recipe = read_yaml(os.path.join(PROJECT_ROOT, "..", "structured_recipes", f"{'bruschetta'}.yaml"))
    unstructured_recipe = load_unstructured_text_test_recipe()
    validator.validate(structured_recipe, unstructured_recipe)
