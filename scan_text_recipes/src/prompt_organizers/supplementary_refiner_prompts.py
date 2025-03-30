from typing import List, Dict

from scan_text_recipes.src.postprocessors.recipe_fixers.supplementary_fixers import SupplementaryPromptQuestion
from scan_text_recipes.src.prompt_organizers.default_prompt_container import DefaultPromptsContainer


class SupplementaryRefinerPromptsContainer(DefaultPromptsContainer):
    def system_prompt(self) -> str:
        return f"""
            You are a helpful assistant that fixes structured recipe generated from recipe text
             by finding missed information in original text. The recipes are in {self.language} language.
        """

    @staticmethod
    def user_recipe_prompt(recipe_text: str, **kwargs) -> str:
        questions: List[SupplementaryPromptQuestion] = kwargs.get('questions')
        refinement_prompt = f"""
            I need to find missing information in the original text.
            Here is the original text:
            *** 
            {recipe_text}.
            ***
            
            Provide answers to next questions in a list of exact order as presented and in exact specified format:
        """
        text_questions = "\n".join(["Q: " + question.question + "\nA: " + question.format_text for question in questions])
        refinement_prompt += text_questions + "\n"
        return refinement_prompt

    def assistant_prompt(self, **kwargs) -> str:
        """
        Create a prompt for the assistant.
        :return: Prompt for the assistant.
        """
        return f"""
        Instructions:
            - If value not found, leave the field empty.
            - ** Respond only in provided form **.
            - The response should be in original recipe language
            """
