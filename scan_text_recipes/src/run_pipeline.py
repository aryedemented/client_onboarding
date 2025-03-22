import os
from typing import Dict

from scan_text_recipes import PROJECT_ROOT
from scan_text_recipes.src import PRE_PROCESSORS_PACKAGE_PATH, MAIN_PROCESSORS_PACKAGE_PATH, \
    POST_PROCESSORS_PACKAGE_PATH, DB_PACKAGE_PATH
from scan_text_recipes.src.db_interface.db_interface import BaseDatabaseInterface
from scan_text_recipes.src.main_processors.recipe_formatter import BaseMainProcessor
from scan_text_recipes.src.postprocessors.recipe_fixers.default_fixers import PostProcessor
from scan_text_recipes.src.preprocessors.preprocessors import PreProcessor
# from scan_text_recipes.tests.examples_for_tests import load_unstructured_text_test_recipe, load_structured_test_recipe
from scan_text_recipes.utils.utils import read_jinja_config, read_yaml, initialize_pipeline_segments, read_text, \
    load_or_create_instance
from scan_text_recipes.utils.visualize_recipe import create_recipe_graph


class ReadRecipePipeline:
    def __init__(
            self,
            bundle_config_path: str,    # path to the bundle config, user-related config
            model_api_keys_path: str,   # connect configuration file - connect to model
            db_connection_config_path: str,  # database connection configuration file
            pipeline_config_path: str = None,  # processing pipeline config, lists of available post, pre and main processors
            model_config_path: str = None,  # LLM properties configuration file
    ):
        # read jinja config
        pipeline_config_path = pipeline_config_path if pipeline_config_path else os.path.join(PROJECT_ROOT, "config", "pipeline_config.yaml")
        model_config_path = model_config_path if model_config_path else os.path.join(PROJECT_ROOT, "config", "model_config.yaml")

        # Init Pipeline Config
        self.pipeline_props = read_jinja_config(pipeline_config_path, bundle_config_path)
        pipeline_segments = self.pipeline_props.pop('PROCESSING_PIPELINE')
        db_interface_config = self.pipeline_props.pop('DATABASE_INTERFACE')

        # Init Model Interface
        self.model_config = read_yaml(model_config_path)
        self.model_api_keys = read_yaml(model_api_keys_path)

        # Init Pipeline
        # Init Preprocessors
        self.pre_processors = initialize_pipeline_segments(
            package_path=PRE_PROCESSORS_PACKAGE_PATH,
            segment_config=pipeline_segments['PRE_PROCESSORS'],
            class_type=PreProcessor,
            **self.pipeline_props
        )

        # Init Main Processors
        self.main_processor = initialize_pipeline_segments(
            package_path=MAIN_PROCESSORS_PACKAGE_PATH,
            segment_config=[pipeline_segments['PROCESSOR']],
            class_type=BaseMainProcessor,
            **self.pipeline_props
        )[0]
        # Init Postprocessors
        self.post_processors = initialize_pipeline_segments(
            package_path=POST_PROCESSORS_PACKAGE_PATH,
            segment_config=pipeline_segments['POST_PROCESSORS'],
            class_type=PostProcessor,
            **self.pipeline_props
        )

        # Init Database Connection
        self.db_interface = load_or_create_instance(
            db_interface_config, BaseDatabaseInterface, DB_PACKAGE_PATH,
            **{'db_connect_config': db_connection_config_path}
        )

    def run_pipeline(self, recipe_text: str) -> [bool, Dict]:
        """
        Run the pipeline on the given recipe dictionary and text.
        """
        # Run all preprocessor
        res = True
        original_text = recipe_text
        for pre_processor in self.pre_processors:
            res, recipe_text = pre_processor.process_recipe(recipe_text)
            if not res:
                return False, {}
        # Run the main processor
        res, recipe_dict = self.main_processor.process_recipe(recipe_text)
        if not res:
            return False, recipe_dict
        # recipe_dict = load_structured_test_recipe()

        # Run all postprocessors
        for post_processor in self.post_processors:
            res, recipe_dict = post_processor.process_recipe(recipe_dict=recipe_dict, recipe_text=original_text)
            if not res:
                return False, recipe_dict
        # Save processed recipe to database
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
    client_name = "italiano"
    bundle_config = os.path.join(PROJECT_ROOT, "client_configs", client_name, "bundle_config.yaml")
    # Model config
    model_api_keys = os.path.join(PROJECT_ROOT, "config", "api_keys.yaml")
    # Database config
    db_connection_config = os.path.join(PROJECT_ROOT, "config", "db_connect_config.yaml")

    pipeline = ReadRecipePipeline(
        bundle_config,
        model_api_keys,
        db_connection_config
    )
    # loaded_recipe_text = read_text(os.path.join(PROJECT_ROOT, "..", "recipes", client_name, "pizza_italiano.txt"))
    loaded_recipe_text = read_text(os.path.join(PROJECT_ROOT, "..", "recipes", client_name, "hamin.txt"))
    # Run the pipeline on the recipe text
    _, processed_recipe = pipeline.run_pipeline(loaded_recipe_text)
    # Save the processed recipe to the database
    pipeline.save_recipe_to_db(processed_recipe, loaded_recipe_text)
    print(processed_recipe)
    graph = create_recipe_graph(processed_recipe)
    graph.render(os.path.join(PROJECT_ROOT, "..", "structured_recipes", "tmp"), view=True)  # Saves and opens the graph
