# Use these examples for tests
import os
from typing import Dict

from scan_text_recipes import PROJECT_ROOT
from scan_text_recipes.utils.utils import read_yaml, read_text


def load_unstructured_text_test_recipe() -> str:
    """
    Load an unstructured test example from a YAML file.
    :return: Unstructured recipe as a string.
    """
    # Define the path to the YAML file
    text_file_path = os.path.join(PROJECT_ROOT, "tests", "classic_pancakes.txt")

    # Load the YAML file
    return read_text(text_file_path)


def load_structured_test_recipe():
    """
    Load a structured test example from a YAML file.
    :return: Structured recipe as a dictionary.
    """
    # Define the path to the YAML file
    yaml_file_path = os.path.join(PROJECT_ROOT, "tests", "classic_pancakes.yaml")

    # Load the YAML file
    return read_yaml(yaml_file_path)


def load_complex_text_test_recipe() -> str:
    text_file_path = os.path.join(PROJECT_ROOT, "tests", "pizza_complex.txt")
    return read_text(text_file_path)


def load_test_architecture_config():
    """
    Load the architecture configuration from a YAML file.
    :return: Architecture configuration as a dictionary.
    """
    # Define the path to the YAML file
    yaml_file_path = os.path.join(PROJECT_ROOT, "tests", "test_architecture_config.yaml")

    # Load the YAML file
    return read_yaml(yaml_file_path)


def load_test_setup_config() -> Dict:
    # Define the path to the YAML file
    yaml_file_path = os.path.join(PROJECT_ROOT, "tests", "test_setup_config.yaml")

    # Load the YAML file
    return read_yaml(yaml_file_path)
