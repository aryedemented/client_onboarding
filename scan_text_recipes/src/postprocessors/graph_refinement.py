import copy
from typing import Dict, List, Union

from torch.utils._cxx_pytree import kwargs

from scan_text_recipes.src import MODEL_INTERFACE_PACKAGE_PATH
from scan_text_recipes.src.model_interface.remote_model_interface import ModelInterface
from scan_text_recipes.src.postprocessors.post_processors import PostProcessor
from scan_text_recipes.src.prompt_organizers.graph_structure_refinement_prompts import Issue, GraphEdgesPromptsContainer
from scan_text_recipes.utils.utils import load_or_create_instance


class GraphRefinement(PostProcessor):
    def __init__(self, config: dict, model_interface: ModelInterface):
        super().__init__(config)
        self.prompts = GraphEdgesPromptsContainer(config["setup_config"], config["language"])
        self.model_interface = load_or_create_instance(
            model_interface, ModelInterface, MODEL_INTERFACE_PACKAGE_PATH, **kwargs
        )

    @staticmethod
    def check_all_ingredients_in_final_dish(recipe_dict: Dict[str, List], recipe_text: str) -> [bool, Dict[str, List]]:
        return Issue(
            "The graph does not end in a single final dish node.",
            "Fix the graph so all nodes lead to a final product"
        )

    @staticmethod
    def check_all_resources_connectivity(recipe_dict: Dict[str, List], recipe_text: str) -> [bool, Dict[str, List]]:
        all_edges_valid = True
        for resource in recipe_dict["resources"]:
            if resource["name"] not in recipe_dict["edges"]:
                all_edges_valid = False
        if all_edges_valid:
            return None
        else:
            return Issue(
                "The graph does not use all resources in the recipe.",
                "Fix the graph so all resources are used in the recipe."
            )

    @staticmethod
    def check_all_ingredients_connectivity(recipe_dict: Dict[str, List], recipe_text: str) -> [bool, Dict[str, List]]:
        all_edges_valid = True
        for ingredient in recipe_dict["ingredients"]:
            if ingredient["name"] not in recipe_dict["edges"]:
                all_edges_valid = False
        if all_edges_valid:
            return None
        else:
            return Issue(
                "The graph does not use all ingredients in the recipe.",
                "Fix the graph so all ingredients are used in the recipe."
            )

    @staticmethod
    def check_resource_ingredient_connectivity(recipe_dict: Dict[str, List], recipe_text: str) -> Union[None, Issue]:
        all_edges_valid = True
        for edge in recipe_dict["edges"]:
            if edge["from"] in recipe_dict["resources"] and edge["to"] in recipe_dict["resources"]:
                all_edges_valid = False
            if edge["from"] in recipe_dict["ingredients"] and edge["to"] in recipe_dict["ingredients"]:
                all_edges_valid = False
        if all_edges_valid:
            return None
        else:
            return Issue(
                "The graph does not use all ingredients in the recipe.",
                "Fix the graph so all ingredients are used in the recipe.")

    def process_recipe(self, recipe_dict: Dict[str, List], recipe_text: str, **kwargs) -> [bool, Dict[str, List]]:
        """
        go over all graph edges in the recipe and see if
        they either start in resource and end in ingredient or vice versa
        :param recipe_dict:
        :param recipe_text:
        :param kwargs:
        :return:
        """

        issues = [
            self.check_resource_ingredient_connectivity(recipe_text=recipe_text, recipe_dict=recipe_dict),
            self.check_all_ingredients_in_final_dish(recipe_text=recipe_text, recipe_dict=recipe_dict),
            self.check_all_resources_connectivity(recipe_text=recipe_text, recipe_dict=recipe_dict),
            self.check_all_ingredients_connectivity(recipe_text=recipe_text, recipe_dict=recipe_dict),
        ]

        issues = [issue for issue in issues if issue is not None]
        for issue in issues:
            self.logger.warning(f"Problem found in recipe graph: {issue.problem}")
            self.logger.warning(f"Asking for solution: {issue.solution}")

        if len(issues) > 0:
            user_prompt = self.prompts.user_recipe_prompt(
                list_of_issues=issues,
                recipe_text=recipe_text,
                recipe_dict=recipe_dict,
            )

            messages = [
                {"role": "system", "content": self.prompts.system_prompt()},
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": self.prompts.assistant_prompt()}
            ]
            res, refined_section = self.model_interface.get_structured_answer(messages=messages)
            return res, refined_section
        else:
            self.logger.info("No issues found in recipe graph.")
            return True, recipe_dict
