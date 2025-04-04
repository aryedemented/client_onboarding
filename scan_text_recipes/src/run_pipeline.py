from pathlib import Path
from dotenv import load_dotenv
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

import os
from typing import Dict

from dotenv import load_dotenv

from scan_text_recipes import PROJECT_ROOT
from scan_text_recipes.src import PRE_PROCESSORS_PACKAGE_PATH, MAIN_PROCESSORS_PACKAGE_PATH, \
    POST_PROCESSORS_PACKAGE_PATH, DB_PACKAGE_PATH, LOGGER_PACKAGE_PATH
from scan_text_recipes.src.db_interface.db_interface import BaseDatabaseInterface
from scan_text_recipes.src.main_processors.recipe_formatter import BaseMainProcessor
from scan_text_recipes.src.postprocessors.recipe_fixers.default_fixers import PostProcessor
from scan_text_recipes.src.preprocessors.preprocessors import PreProcessor
from scan_text_recipes.utils.logger.basic_logger import BaseLogger
# from scan_text_recipes.tests.examples_for_tests import load_unstructured_text_test_recipe, load_structured_test_recipe
from scan_text_recipes.utils.utils import read_jinja_config, read_yaml, initialize_pipeline_segments, read_text, \
    load_or_create_instance, write_yaml
from scan_text_recipes.utils.visualize_recipe import create_recipe_graph


class ReadRecipePipeline:
    def __init__(
            self,
            client_config_path: str,    # path to the bundle config, user-related config
            model_api_keys_path: str,   # connect configuration file - connect to model
            db_connection_config_path: str,  # database connection configuration file
            pipeline_config_path: str = None,  # processing pipeline config, lists of available post, pre and main processors
            model_config_path: str = None,  # LLM properties configuration file
            logger: BaseLogger = None
    ):
        # read jinja config
        pipeline_config_path = pipeline_config_path if pipeline_config_path else os.path.join(PROJECT_ROOT, "config", "pipeline_config.yaml")
        model_config_path = model_config_path if model_config_path else os.path.join(PROJECT_ROOT, "config", "model_config.yaml")

        # Init Pipeline Config
        self.client_pipeline_config = read_jinja_config(pipeline_config_path, client_config_path)
        pipeline_segments = self.client_pipeline_config.pop('PROCESSING_PIPELINE')
        db_interface_config = self.client_pipeline_config.pop('DATABASE_INTERFACE')

        # Init Logger
        if 'logger' in self.client_pipeline_config:
            self.client_pipeline_config['logger'] = logger if logger else self.client_pipeline_config['logger']
            self.logger = load_or_create_instance(
                self.client_pipeline_config['logger'], BaseLogger, LOGGER_PACKAGE_PATH, name=self.__class__.__name__,
            )
        # Init Model Interface
        self.model_config = read_yaml(model_config_path)
        self.model_api_keys = read_yaml(model_api_keys_path)

        # Init Pipeline
        # Init Preprocessors
        self.pre_processors = initialize_pipeline_segments(
            package_path=PRE_PROCESSORS_PACKAGE_PATH,
            segment_config=pipeline_segments['PRE_PROCESSORS'],
            class_type=PreProcessor,
            **self.client_pipeline_config
        )

        # Init Main Processors
        self.main_processor = initialize_pipeline_segments(
            package_path=MAIN_PROCESSORS_PACKAGE_PATH,
            segment_config=[pipeline_segments['PROCESSOR']],
            class_type=BaseMainProcessor,
            **self.client_pipeline_config
        )[0]
        # Init Postprocessors
        self.post_processors = initialize_pipeline_segments(
            package_path=POST_PROCESSORS_PACKAGE_PATH,
            segment_config=pipeline_segments['POST_PROCESSORS'],
            class_type=PostProcessor,
            **self.client_pipeline_config
        )

        # Init Database Connection
        self.db_interface = load_or_create_instance(
            db_interface_config, BaseDatabaseInterface, DB_PACKAGE_PATH,
            **{'db_connect_config': db_connection_config_path},
            **self.client_pipeline_config
        )

    def run_pipeline(self, recipe_text: str) -> [bool, Dict]:
        """
        Run the pipeline on the given recipe dictionary and text.
        """
        # Run all preprocessor
        original_text = recipe_text
        self.logger.info(f'Running Pre-Processors on textual data:')
        for pre_processor in self.pre_processors:
            res, recipe_text = pre_processor.process_recipe(recipe_text)
            if not res:
                return False, {}
        # Run the main processor
        self.logger.info(f'Running Main Processor (text to structured recipe):')
        res, recipe_dict = self.main_processor.process_recipe(recipe_text)
        if not res:
            return False, recipe_dict
        # recipe_dict = load_structured_test_recipe()

        # Run all postprocessors
        self.logger.info(f'Running Post-Processors on structured recipe:')
        for post_processor in self.post_processors:
            self.logger.warning(f'Running: {post_processor.__class__.__name__}')
            res, recipe_dict = post_processor.process_recipe(recipe_dict=recipe_dict, recipe_text=original_text)
            if not res:
                return False, recipe_dict
        # Save processed recipe to database
        self.logger.log(f'Finished processing recipe')
        return res, recipe_dict

    def save_recipe_to_db(self, recipe_dict: Dict, recipe_text: str):
        """
        Save the processed recipe to the database.
        """
        # Save the recipe to the database
        pass


if __name__ == '__main__':
    # Example usage
    # Client - related information
    client_name = os.environ.get("CLIENT_NAME")
    client_config = os.path.join(PROJECT_ROOT, "client_configs", client_name, "client_config.yaml")
    # Model config
    model_api_keys = os.path.join(PROJECT_ROOT, "config", "api_keys.yaml")
    # Database config
    db_connection_config = os.path.join(PROJECT_ROOT, "config", "db_connect_config.yaml")

    pipeline = ReadRecipePipeline(
        client_config,
        model_api_keys,
        db_connection_config
    )

    loaded_recipe_text = read_text(os.path.join(PROJECT_ROOT, "..", "recipes", client_name, "bruschetta.txt"))
    # loaded_recipe_text = read_text(os.path.join(PROJECT_ROOT, "..", "recipes", client_name, "hamin.txt"))
    # Run the pipeline on the recipe text
    _, processed_recipe = pipeline.run_pipeline(loaded_recipe_text)
    # Save the processed recipe to the database
    pipeline.save_recipe_to_db(processed_recipe, loaded_recipe_text)
    write_yaml(processed_recipe, os.path.join(PROJECT_ROOT, "..", "structured_recipes", f"{'bruschetta'}.yaml"), encoding='utf-8')
    print(processed_recipe)
    graph = create_recipe_graph(processed_recipe)
    graph.render(os.path.join(PROJECT_ROOT, "..", "structured_recipes", "tmp"), view=True)  # Saves and opens the graph
