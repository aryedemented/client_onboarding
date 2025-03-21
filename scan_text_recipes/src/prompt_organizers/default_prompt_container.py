from scan_text_recipes.src.prompt_organizers.base_prompts_container import BasePromptsContainer


class DefaultPromptsContainer(BasePromptsContainer):
    @staticmethod
    def system_prompt() -> str:
        return """
            You are a helpful assistant that extracts and structures recipes into a JSON format.
        """

    def force_ingredients_prompt(self) -> str:
        return f"""
            - Allowed ingredient are: [{self.config['ALLOWED_INGREDIENTS']}].
        """ if self.force_ingredients else ""

    def force_resources_prompt(self) -> str:
        return f"""
            - Allowed resources are: [{self.config['ALLOWED_RESOURCES']}].
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
    - Edges will have instructions explaining the process, that will be derived form the recipe and added as properties of the edges 
    - Every Ingredient should be connected to the resource it is used in, and every resource should be connected to all ingredients used in it.
    - There should be no ingredient-to-ingredient or resource-to resource connections, all connections are either resource-to-ingredient or ingredient-to-resource.
    Now extract this JSON for the given recipe: 
    """

    @staticmethod
    def assistant_prompt(*args, **kwargs) -> str:
        return """
    Your response must be **only JSON**. **Return JSON only**, with no text before or after.

    ### Expected JSON format **be exact with field names**:
    {
        "ingredients": [
            {"name": "flour", "quantity": "1 cup", "remarks": "instruction on how to use flour, if mentioned in the recipe, else leave blank"},
            {"name": "sugar", "quantity": "2 tbsp", "remarks": "instruction on how to use sugar, if mentioned in the recipe, else leave blank"},
            {"name": "dough", "quantity": "combined", "remarks": "instruction on how dough is created, if mentioned in the recipe, else leave blank"},
        ],
        "resources": [
            {"name": "oven", "preparation_time": "10 min", "remarks" "instruction on how to bake in the oven, if mentioned in the recipe, else leave blank"},
        ],
        "edges": [
            {"from": "flour", "to": "dough", "instructions": "instruction on how flour is utilized in the dough, if mentioned in the recipe, else leave blank"},
            {"from": "sugar", "to": "dough", "instructions": "instructions on how sugar is utilized in the dough, if mentioned in the recipe, else leave blank"},
            {"from": "dough", "to": "oven", "instructions": "instructions on how dough is utilized in oven, if mentioned in the recipe, else leave blank"},
        ]
    }
    ###
    """
