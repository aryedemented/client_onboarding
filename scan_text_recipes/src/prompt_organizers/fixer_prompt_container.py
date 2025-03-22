from typing import Dict, List

from scan_text_recipes.src.prompt_organizers.default_prompt_container import DefaultPromptsContainer


class DefaultRefinerPromptsContainer(DefaultPromptsContainer):
    @staticmethod
    def user_recipe_prompt(recipe_text: str, **kwargs) -> str:
        section_name: str = kwargs.get('section_name')
        section: List[Dict] = kwargs.get('section')
        refinement_prompt = f"""
            I have an extracted structured response, but some {section_name} fields are missing or incorrect.
            Please complete the missing values based on the original text.
            Here is the structured response: {{{section}}}.
            Here is the original text: [{recipe_text}].
        """
        return refinement_prompt

    def assistant_prompt(self, **kwargs) -> str:
        """
        Create a prompt for the assistant.
        :return: Prompt for the assistant.
        """
        return f"""
        Instructions:
            - Address fields encapsulated in "$$$" and fix the values according to instructions.
            - Preserve the existing structure.
            - If value not found, leave the field empty.
            - **Respond only with the updated JSON**.
            - Field names should be in english, but the values should be in the original language of the recipe.
            """
