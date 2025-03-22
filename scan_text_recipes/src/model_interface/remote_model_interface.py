import os
from abc import abstractmethod
from typing import Dict, List

import openai
import json

from openai.types.chat import ChatCompletion
from scan_text_recipes import PROJECT_ROOT
from scan_text_recipes.src import LOGGER_PACKAGE_PATH
from scan_text_recipes.src.prompt_organizers.default_prompt_container import DefaultPromptsContainer
from scan_text_recipes.tests.examples_for_tests import load_unstructured_text_test_recipe, load_test_setup_config
from scan_text_recipes.utils.logger.basic_logger import BaseLogger
from scan_text_recipes.utils.utils import read_api_key, clean_json_output, write_yaml, read_model_config, \
    load_or_create_instance


class ModelInterface:
    def __init__(self, config: Dict = None, logger=None, **kwargs):
        self.model_config: Dict = config if config else read_model_config()
        self.logger = load_or_create_instance(
            logger, BaseLogger, LOGGER_PACKAGE_PATH, **{**{"name": self.__class__.__name__}, **kwargs}
        )

    @abstractmethod
    def get_structured_answer(self, messages: List[Dict]) -> Dict:
        ...

    @abstractmethod
    def get_text_answer(self, messages: List[Dict]) -> str:
        ...

    @staticmethod
    def save_formatted_recipe(recipe_dict, filename):
        write_yaml(recipe_dict, os.path.join(PROJECT_ROOT, "..", "formatted_recipes", f"{filename}.yaml"))

    @staticmethod
    def get_number_of_tokens_from_the_text(text: str) -> int:
        """
        Get the number of tokens from the text. NOTE: use count of words instead and multiply by 1.5
        """
        return int(len(text.split(" ")) * 1.5)


class RemoteAPIModelInterface(ModelInterface):
    def __init__(self, config: Dict = None, **kwargs):
        super().__init__(config if config else read_model_config(), **kwargs)
        self.client = openai.OpenAI(
            api_key=read_api_key(self.model_config['API_KEY_NAME']),
            base_url=self.model_config['BASE_URL']
        )

    def get_response(self, messages: List[Dict]) -> ChatCompletion:
        self.logger.info("Sending request to the model...")
        return self.client.chat.completions.create(
            model=self.model_config["MODEL_NAME"],
            messages=messages,
            top_p=self.model_config['TOP_P'],
            temperature=self.model_config['TEMPERATURE'],
            logprobs=self.model_config['LOGPROBS'],
            top_logprobs=self.model_config['TOP_LOGPROBS']
        )

    def get_structured_answer(self, messages: List[Dict]) -> [bool, Dict]:
        response = self.get_response(messages)
        # Extract response
        try:
            formatted_recipe = clean_json_output(response.choices[0].message.content)
            response = json.loads(formatted_recipe)
            self.logger.info("Recipe processed successfully")
            return True, response
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON response: {json.JSONDecodeError}")
            return False, {}

    def get_text_answer(self, messages: List[Dict]) -> [bool, str]:
        try:
            response = self.get_response(messages)
            content = response.choices[0].message.content
            self.logger.info("Received valid reply")
            return True, content
        except Exception as e:
            self.logger.error(f"Error occurred in response: {e}")
            print()
            return False, ""


if __name__ == '__main__':
    model_config = read_model_config()
    # Test the model interface
    recipe = load_unstructured_text_test_recipe()
    model_interface = RemoteAPIModelInterface(config=model_config)
    # initialize prompt container
    prompts = DefaultPromptsContainer(load_test_setup_config(), language="English")
    msgs = [
        {"role": "system", "content": prompts.system_prompt()},
        {"role": "user", "content": prompts.user_recipe_prompt(recipe)},
        {"role": "assistant", "content": prompts.assistant_prompt()}
    ]
    extracted_recipe = model_interface.get_structured_answer(messages=msgs)
    print(extracted_recipe)
