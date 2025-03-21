from scan_text_recipes.src.prompt_organizers.base_prompts_container import BasePromptsContainer


class SimplifierPromptsContainer(BasePromptsContainer):
    """
    This class contains the prompts used for the simplifier.
    """

    def system_prompt(self) -> str:
        return f"""
        You are a text simplifier, trained to simplify cooking recipes texts in {self.language}.
        """

    @staticmethod
    def user_recipe_prompt(recipe_text: str, **kwargs) -> str:
        return f"""
        I have a cooking recipe text that is too long and complex. Please simplify it.
        Here is the original text: [{recipe_text}].
        """

    @staticmethod
    def assistant_prompt(**kwargs) -> str:
        return f"""
        Instructions:
            - Simplify the text to make it easier to understand.
            - Preserve the original meaning and context.
            - Ensure that the simplified text is clear and concise.
            - Do not add any new information or change the original meaning.
            - ** Return ONLY the simplified text.** Do not add any other text.
        """

