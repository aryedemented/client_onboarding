import json
import os
from inspect import isabstract
from typing import Dict, List, Dict, Any, Type
from ruamel.yaml import YAML

from jinja2 import Environment, FileSystemLoader, Template
import psycopg2


from scan_text_recipes import PROJECT_ROOT
import yaml
from easydict import EasyDict as easy_dict

from scan_text_recipes.utils.file_utils import dynamic_import_from_packages


def read_yaml(filename: str, **kwargs) -> Dict:
    with open(filename, 'r', encoding="utf-8", **kwargs) as file:
        data = yaml.safe_load(file)
    return data


def write_yaml(data_dict, filename: str, **kwargs):
    with open(filename, 'w', **kwargs) as file:
        yaml.dump(data_dict, file, default_flow_style=False, allow_unicode=True)


def read_api_key(key_name) -> str:
    keys_dict = read_yaml(os.path.join(PROJECT_ROOT, "config", "api_keys.yaml"))
    return keys_dict[key_name]


def clean_json_output(text):
    txt = text.strip("```")
    txt = txt.strip("json") if txt.startswith("json") else text
    return txt


def read_config() -> Dict:
    keys_dict = read_yaml(os.path.join(PROJECT_ROOT, "config", "db_connect_config.yaml"))
    return easy_dict(keys_dict)


def read_model_config() -> Dict:
    keys_dict = read_yaml(os.path.join(PROJECT_ROOT, "config", "model_config.yaml"))
    current_model = keys_dict['CURRENT_MODEL']
    return easy_dict(keys_dict['MODEL'][current_model])


def load_yaml_without_comments(yaml_path):
    """
    Loads a YAML file while ignoring comments using ruamel.yaml.
    """
    yaml = YAML(typ="safe")  # "safe" mode avoids preserving comments
    with open(yaml_path, "r", encoding="utf-8") as file:
        data = yaml.load(file)  # Ignores comments automatically
    return data


def read_schema_config() -> Dict:
    """
    Load a YAML file, process Jinja templates, and return a dictionary.
    """
    # Step 1: Read YAML file as raw text (Jinja placeholders exist)
    yaml_loader = YAML(typ="safe")  # "safe" mode ignores comments
    with open(os.path.join(PROJECT_ROOT, "config", "db_config.yaml"), "r", encoding="utf-8") as file:
        yaml_data = yaml_loader.load(file)  # ✅ Ignores comments

    # Step 2: Extract categorical definitions for Jinja processing
    extracted_values = yaml_data.get("CATEGORIES", {})

    # Step 3: Convert the full YAML back to a string for Jinja rendering
    raw_yaml_str = yaml.dump(yaml_data)  # ✅ Convert to string for Jinja processing

    # Step 4: Process Jinja placeholders
    template = Template(raw_yaml_str)
    rendered_yaml = template.render(**extracted_values)

    # Step 5: Load YAML again after Jinja processing
    final_schema = yaml.safe_load(rendered_yaml)  # ✅ Final parsed schema
    return final_schema


def read_jinja_config(config_file: str, template_file: str) -> Dict:
    with open(config_file, encoding='utf-8') as f_config:
        config_data = f_config.read()  # ✅ Ignores comments
    with open(template_file, encoding='utf-8') as f_template:
        yaml_template = f_template.read()

    rendered_variables = Template(yaml_template).module.__dict__

    # Create Jinja template and render
    template = Template(config_data)
    rendered_yaml = template.render(rendered_variables)
    return yaml.safe_load(rendered_yaml)


def get_available_models(client):
    response = client.models.list()
    for model in response.data:
        print(model.id)


def read_text(filename) -> str:
    with open(filename, "r", encoding="utf-8") as file:
        content = file.read()
    return content


# Connect using psycopg2
def get_connection(db_connect_config):
    return psycopg2.connect(**db_connect_config)


def execute_query(connection, cursor, query, *args, **kwargs):
    cursor.execute(query, *args, **kwargs)
    connection.commit()
    if cursor.description is not None:
        return cursor.fetchall()
    return None


def list_it(data: Any) -> List:
    """
    Convert a non-list object to a list.
    :param data:
    :return:
    """
    if not isinstance(data, list):
        return [data]
    return data


def initialize_pipeline_segments(package_path: str, segment_config: List, class_type: Type[Any], **kwargs) -> List:
    processor_classes = dynamic_import_from_packages(
        [package_path],
        lambda x: issubclass(x, class_type) and not isabstract(x)
    )
    processors = []
    for proc_props in segment_config:
        name = next(iter(proc_props))
        props = proc_props.get(name, {})
        if not isinstance(props, dict):
            props = {}
        processors.append(processor_classes[name](**{**props, **kwargs}))  # Priority to props, i.e. to specific class properties
    return processors


def load_or_create_instance(input_, class_: Type, package_path: str, **kwargs):
    if isinstance(input_, class_) or input_ is None or len(input_) == 0:
        return input_
    if isinstance(input_, str):
        input_config = list_it({input_: {}})
    else:
        input_config = list_it(input_)
    instance = initialize_pipeline_segments(
        package_path=package_path,
        segment_config=input_config,
        class_type=class_,
        **kwargs
    )[0]
    return instance
