from dataclasses import dataclass
from typing import List

from scan_text_recipes.src.prompt_organizers.default_prompt_container import DefaultPromptsContainer


@dataclass
class Issue:
    problem: str
    solution: str


class GraphEdgesPromptsContainer(DefaultPromptsContainer):
    def system_prompt(self) -> str:
        return f"""
            You are a helpful assistant that fixes errors in recipe graphs generated from recipe text in {self.language} language.
        """

    @staticmethod
    def user_recipe_prompt(recipe_text: str, list_of_issues: List[Issue] = None, **kwargs) -> str:
        assert list_of_issues is not None, "list_of_issues should not be None. If there are no issues, the code should not get here."
        assert "recipe_dict" in kwargs, "recipe_dict should be in kwargs."
        recipe_dict = kwargs.get('recipe_dict')
        problems = "\n- ".join([issue.problem for issue in list_of_issues])
        solutions = "\n- ".join([issue.solution for issue in list_of_issues])
        refinement_prompt = f"""
            "Here is a recipe and a recipe graph. The graph has some issues:
            
            Please address these issues: {problems} 
            These are the required solutions: {solutions}
            Here is the graph: ***\n{recipe_dict}\n***.
            Here is the original text: ***\n{recipe_text}***\n.
            
            - **Respond only with the updated JSON** Do not add any explanations or remarks.
            - Field names should be in english, but the values should be in the original language of the recipe.
        """
        return refinement_prompt

    def assistant_prompt(self, **kwargs) -> str:
        """
        Create a prompt for the assistant.
        :return: Prompt for the assistant.
        """
        return f"""
        Graph Structure:
            - Recipe Graphs provided in format where nodes can be of two kinds: ingredient or resources.
            - ingredient nodes represent the ingredients used in the recipe. The properties include the name, quantity, and remarks.
            - resource nodes represent the resources used in the recipe. The properties include the name, preparation time, and remarks.
            - edges describe the relationship between resources and ingredients.
            - Graph is of a DAG structure, meaning that there are no cycles in the graph.
            - Graph final node named {self.setup_config['FINAL_NODE_NAME']}.
            """
