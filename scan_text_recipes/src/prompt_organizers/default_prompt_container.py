from scan_text_recipes.src.prompt_organizers.base_prompts_container import BasePromptsContainer


class DefaultPromptsContainer(BasePromptsContainer):
    def system_prompt(self) -> str:
        return f"""
            You are a helpful assistant that extracts and structures recipes in {self.language} into a JSON format.
        """

    def force_ingredients_prompt(self) -> str:
        return f"""
            - Allowed ingredient are: {list(self.setup_config['ALLOWED_INGREDIENTS'].keys())}.
        """ if self.force_ingredients else ""

    def force_resources_prompt(self) -> str:
        return f"""
            - Allowed resources are: {list(self.setup_config['ALLOWED_RESOURCES'].keys())}.
        """ if self.force_resources else ""

    def user_recipe_prompt(self, recipe_text: str, **kwargs) -> str:
        return f"""
    Convert the following recipe into a structured JSON format using a DAG-like representation:

    Recipe:
    {recipe_text}

    Ensure that:
    - Extract the necessary ingredients and their quantities
    - Extract large kitchen tools (a.k.a resources) used in preparation such as ovens, stoves, refrigerators, mixers, blenders etc...
    - Structure the preparation steps in a Directed Acyclic Graph (DAG).
    {self.force_ingredients_prompt()}
    - Represent ingredients and intermediate ingredients (i.e. created in the process) as nodes of the graph.
    - Represent ingredients quantities as property of the ingredient nodes.
    {self.force_resources_prompt()}
    - Represent resources also as nodes with preparation time and temperature (if applicable) as properties
    - Represent resource preparation time as properties of resource nodes. 
    - Combining / adding ingredients into resources will be represented as edges
    - Final Node should have name {self.setup_config['FINAL_NODE_NAME']}.
    - Edges will have instructions explaining the process, that will be derived form the recipe and added as properties of the edges.
    - Every Ingredient should be connected to the resource it is used in.
    - Every Resource should be connected to all ingredients used in it, and have at least one outgoing edge connection to ingredient node.
    - There should be no ingredient-to-ingredient or resource-to-resource edges connections, all edges connections are either resource-to-ingredient or ingredient-to-resource.
    - Field names should be in english, but the values should be in the original language of the recipe.
    - Enumerate the ingredients and resources nodes starting from 0 and save them as id of the node. While names of resources and ingredients does not have to be unique, the "id" of nodes should be unique.
    Now extract this JSON for the given recipe: 
    """

    @staticmethod
    def assistant_prompt(*args, **kwargs) -> str:
        return """
    Your response must be **only JSON**. **Return JSON only**, with no text before or after.

    ### Expected JSON format **be exact with field names**:
    {
        "ingredients": [
            {"id": 0, "name": "flour", "quantity": "1 cup", "instructions": "instruction on how to use flour, if mentioned in the recipe, else leave blank"},
            {"id": 1, "name": "sugar", "quantity": "2 tbsp", "instructions": "instruction on how to use sugar, if mentioned in the recipe, else leave blank"},
            {"id": 2, "name": "dough", "quantity": "combined", "instructions": "instruction on how dough is created, if mentioned in the recipe, else leave blank"},
        ],
        "resources": [
            {"id": 3, "name": "oven", "usage_time": "10 min", "instructions" "instruction on how to bake in the oven, if mentioned in the recipe, else leave blank"},
        ],
        "edges": [
            {"from": 0, "to": 3, "instructions": "instruction on how flour is utilized in the dough, if mentioned in the recipe, else leave blank"},
            {"from": 1, "to": 3, "instructions": "instructions on how sugar is utilized in the dough, if mentioned in the recipe, else leave blank"},
            {"from": 2, "to": 3, "instructions": "instructions on how dough is utilized in oven, if mentioned in the recipe, else leave blank"},
        ]
    }
    ###
    """
