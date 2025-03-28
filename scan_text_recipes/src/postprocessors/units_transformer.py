import ftplib
from typing import List, Dict, Union

from scan_text_recipes.src.postprocessors.post_processors import PostProcessor
from scan_text_recipes.src.unit_converters.units_extractor import UnitsHandler
from scan_text_recipes.tests.examples_for_tests import load_test_setup_config, load_structured_test_recipe
from scan_text_recipes.utils.utils import read_yaml


class UnitsTransformer(PostProcessor, UnitsHandler):
    def __init__(self, setup_config: Union[str, Dict[str, Dict[str, str]]], language: str = None, **kwargs):
        super().__init__(**kwargs)
        self.setup_config = setup_config if isinstance(setup_config, dict) else read_yaml(setup_config)
        self.allowed_ingredients = self.setup_config.get("ALLOWED_INGREDIENTS")
        self.language = language  # TODO: add language support

    def get_expected_units(self, name):
        return self.allowed_ingredients[name] if name in self.allowed_ingredients else None

    def process_recipe(self, recipe_dict: Dict[str, List], recipe_text: str, **kwargs) -> [bool, Dict[str, List]]:
        """
        Transform the units in the recipe dictionary to the preferred units.
        """
        transformed_recipe = recipe_dict.copy()
        for ingredient in transformed_recipe["ingredients"]:
            expected_unit = self.get_expected_units(ingredient["name"])
            if expected_unit:
                ingredient["units"] = expected_unit
                ingredient["quantity"] = self.to(str(ingredient["quantity"]), expected_unit)
            else:
                ingredient["units"] = ""
                ingredient["quantity"] = self.get_magnitude(ingredient["quantity"])
        return True, transformed_recipe


if __name__ == '__main__':
    # Example usage
    units_transformer = UnitsTransformer(setup_config=load_test_setup_config())
    struct_recipe_dict = load_structured_test_recipe()
    _, transformed_recipe_dict = units_transformer.process_recipe(struct_recipe_dict, "")
    print(transformed_recipe_dict)
