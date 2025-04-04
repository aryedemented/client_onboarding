from typing import List, Dict

from scan_text_recipes.src.issues_class_format import SupplementaryPromptQuestion
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
        text_questions = "\n".join(["Question: " + question.question for question in questions])
        refinement_prompt += text_questions + "\n"
        return refinement_prompt

    def assistant_prompt(self, **kwargs) -> str:
        """
        Create a prompt for the assistant.
        :return: Prompt for the assistant.
        """
        return f"""
        Instructions:
            - If value not found, leave the field empty
            - Convert value if needed to the ** units specified in the question **.
            - IMPORTANT: Even if the original recipe includes units, strip them and return ONLY the number in value field.
            - ** Provides answers in exact order of provided questions **.
            - Encapsulate all answers in one set of square brackets, so it could be read in JSON format
            - Example of Expected Answer:
            [
                {{ "name": "קמח", "value": "1" , "units": "cup"}},
                {{ "name": "סוכר", "value": "2" , "units": "tbsp"}},
                {{ "name": "בצק", "value": "" , "units": ""}},
                {{ "name": "תנור", "value": "10.5" , "units": "min"}},
                ...
            ]
            """
