import copy
from typing import Dict, List, Union

from scan_text_recipes.src import MODEL_INTERFACE_PACKAGE_PATH
from scan_text_recipes.src.model_interface.remote_model_interface import ModelInterface
from scan_text_recipes.src.postprocessors.post_processors import PostProcessor
from scan_text_recipes.src.prompt_organizers.graph_structure_refinement_prompts import Issue, GraphEdgesPromptsContainer
from scan_text_recipes.utils.utils import load_or_create_instance, read_yaml


from typing import Dict, List, Set


def check_node(
        ingredient_name: str, recipe_dict: Dict[str, List], final_node_name: str, visited: Set[str] = None
) -> bool:
    if visited is None:
        visited = set()

    if ingredient_name in visited:
        return False  # Prevent infinite loop

    visited.add(ingredient_name)

    for edge in recipe_dict["edges"]:
        if edge["from"] == ingredient_name:
            if edge["to"] == final_node_name:
                return True
            if check_node(edge["to"], recipe_dict, final_node_name, visited):
                return True

    return False


class GraphRefinement(PostProcessor):
    def __init__(self, setup_config: Union[str, Dict], model_interface: ModelInterface, **kwargs):
        super().__init__(**kwargs)
        self.prompts = GraphEdgesPromptsContainer(setup_config, **kwargs)
        self.model_interface = load_or_create_instance(
            model_interface, ModelInterface, MODEL_INTERFACE_PACKAGE_PATH, **kwargs
        )
        self.setup_config = setup_config if isinstance(setup_config, dict) else read_yaml(setup_config)
        self.final_node_name = self.setup_config.get("FINAL_NODE_NAME")

    def check_all_ingredients_in_final_dish(self, recipe_dict: Dict[str, List], recipe_text: str) -> [bool, Dict[str, List]]:
        """
        Checks recursively that each ingredient in the recipe is connected to a final dish node.
        :param recipe_dict:
        :param recipe_text:
        :return:
        """
        check_node_result = True
        for ingredient in recipe_dict["ingredients"]:
            check_node_result = check_node_result & check_node(ingredient["name"], recipe_dict, self.final_node_name)
        return Issue(
            "Not all ingredients eventually lead to a final dish node.",
            "Fix the graph so all ingredients lead to a final dish node."
        )

    def check_all_resources_in_final_dish(self, recipe_dict: Dict[str, List], recipe_text: str) -> [bool, Dict[str, List]]:
        """
        Checks recursively that each resource in the recipe is connected to a final dish node.
        :param recipe_dict:
        :param recipe_text:
        :return:
        """
        check_node_result = True
        for resource in recipe_dict["resources"]:
            check_node_result = (check_node_result & check_node(resource["name"], recipe_dict, self.final_node_name))
        return Issue(
            "All ingredients used in any of the resources do not lead to a final dish node.",
            "Fix the graph so all that used in resources lead to a final dish node."
        )

    def check_if_final_node_present(self, recipe_dict: Dict[str, List], recipe_text: str) -> [bool, Dict[str, List]]:
        """
        Check if the final node is present in the recipe.
        :param recipe_dict:
        :param recipe_text:
        :return:
        """
        if self.final_node_name in recipe_dict["ingredients"]:
            return Issue(
                "The graph does not end in a single final node.",
                f"Fix the graph so all nodes lead to a final node named  {self.final_node_name}."
            )
        return None

    @staticmethod
    def check_all_resources_connectivity(recipe_dict: Dict[str, List], recipe_text: str) -> [bool, Dict[str, List]]:
        """
            Check if all resources have incoming and outgoing edges -
            i.e. we expect to put something and take something out of every resource.
        """
        all_edges_valid = True
        for resource in recipe_dict["resources"]:
            going_in = resource['name'] in [node["to"] for node in recipe_dict["edges"]]
            going_out = resource['name'] in [node["from"] for node in recipe_dict["edges"]]
            if not( going_in and going_out):
                all_edges_valid = False
        if all_edges_valid:
            return None
        else:
            return Issue(
                "The graph does not use all resources in the recipe.",
                f"""Fix the graph so all resources are used in the recipe.
                For each resource node there should be at least on incoming and one outgoing edge to ingredient nodes."""
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
            self.check_if_final_node_present(recipe_text=recipe_text, recipe_dict=recipe_dict),
            self.check_resource_ingredient_connectivity(recipe_text=recipe_text, recipe_dict=recipe_dict),
            self.check_all_ingredients_in_final_dish(recipe_text=recipe_text, recipe_dict=recipe_dict),
            self.check_all_resources_in_final_dish(recipe_text=recipe_text, recipe_dict=recipe_dict),
            self.check_all_resources_connectivity(recipe_text=recipe_text, recipe_dict=recipe_dict),
            self.check_all_ingredients_connectivity(recipe_text=recipe_text, recipe_dict=recipe_dict)
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
            res, refined_recipe = self.model_interface.get_structured_answer(messages=messages)
            return res, refined_recipe
        else:
            self.logger.info("No issues found in recipe graph.")
            return True, recipe_dict
