import os
from typing import Dict

from scan_text_recipes import PROJECT_ROOT
from scan_text_recipes.src.main_processors.recipe_formatter import BaseMainProcessor
from scan_text_recipes.src.postprocessors.recipe_fixers.default_fixers import PostProcessor
from scan_text_recipes.src.preprocessors.preprocessors import PreProcessor
from scan_text_recipes.utils.utils import read_jinja_config, read_yaml, initialize_pipieline_segments
from scan_text_recipes.utils.visualize_recipe import create_recipe_graph


class ReadRecipePipeline:
    def __init__(
            self,
            bundle_config_path: str,    # path to the bundle config, user-related config
            setup_config_path: str,     # kitchen setup config, lists of available resources and ingredients
            model_api_keys_path: str,   # connect configuration file - connect to model
            db_config_path: str,        # database structure configuration file
            db_connection_config_path: str,  # database connection configuration file

            pipeline_config_path: str = None,  # processing pipeline config, lists of available post, pre and main processors
            model_config_path: str = None,  # LLM properties configuration file
            **kwargs
    ):
        # read jijna config
        pipeline_config_path = pipeline_config_path if pipeline_config_path else os.path.join(PROJECT_ROOT, "config", "pipeline_config.yaml")
        model_config_path = model_config_path if model_config_path else os.path.join(PROJECT_ROOT, "config", "model_config.yaml")

        # Init Pipeline Config
        self.pipeline_props = read_jinja_config(pipeline_config_path, bundle_config_path)
        pipeline_segments = self.pipeline_props.pop('PROCESSING_PIPELINE')

        # Init Model Interface
        self.model_config = read_yaml(model_config_path)
        self.model_api_keys = read_yaml(model_api_keys_path)

        # Init Pipeline
        self.kitchen_setup = read_yaml(setup_config_path)

        # Init Preprocessors
        self.pre_processors = initialize_pipieline_segments(
            package_path="scan_text_recipes.src.preprocessors",
            segment_config=pipeline_segments['PRE_PROCESSORS'],
            class_type=PreProcessor,
            **self.pipeline_props
        )

        # Init Main Processors
        self.main_processor = initialize_pipieline_segments(
            package_path="scan_text_recipes.src.main_processors",
            segment_config=[pipeline_segments['PROCESSOR']],
            class_type=BaseMainProcessor,
            **self.pipeline_props
        )[0]
        # Init Postprocessors
        self.post_processors = initialize_pipieline_segments(
            package_path="scan_text_recipes.src.postprocessors",
            segment_config=pipeline_segments['POST_PROCESSORS'],
            class_type=PostProcessor,
            **self.pipeline_props
        )

        # Init Database Connection
        self.db_config = read_yaml(db_config_path)
        self.db_connection_config = read_yaml(db_connection_config_path)

    def run_pipeline(self, recipe_text: str) -> Dict:
        """
        Run the pipeline on the given recipe dictionary and text.
        """
        # Run all preprocessor
        # Run the main processor
        # Run all postprocessors
        # Run main processor
        # Save processed recipe to database
        pass

    def save_recipe_to_db(self, recipe_dict: Dict, recipe_text: str):
        """
        Save the processed recipe to the database.
        """
        # Save the recipe to the database
        pass


if __name__ == '__main__':
    # Example usage
    # Client - related information
    client_name = "aroma"
    bundle_config = os.path.join(PROJECT_ROOT, "client_configs", client_name, "bundle_config.yaml")
    setup_config = os.path.join(PROJECT_ROOT, "client_configs", client_name, "setup_config.yaml")

    # Model config
    model_api_keys = os.path.join(PROJECT_ROOT, "config", "api_keys.yaml")

    # Database config
    db_config = os.path.join(PROJECT_ROOT, "config", "db_config.yaml")
    db_connection_config = os.path.join(PROJECT_ROOT, "config", "db_connect_config.yaml")

    pipeline = ReadRecipePipeline(
        bundle_config,
        setup_config,
        model_api_keys,
        db_config,
        db_connection_config
    )
    recipe_text = "Example recipe text"
    # Run the pipeline on the recipe text
    processed_recipe = pipeline.run_pipeline(recipe_text)
    # Save the processed recipe to the database
    pipeline.save_recipe_to_db(processed_recipe, recipe_text)
    print(processed_recipe)
    graph = create_recipe_graph(processed_recipe)
    graph.render(os.path.join(PROJECT_ROOT, "..", "structured_recipes", "tmp"), view=True)  # Saves and opens the graph
