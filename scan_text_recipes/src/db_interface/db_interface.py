import os
import re
from typing import Dict, Tuple, List, Union

import numpy as np
import psycopg2

from scan_text_recipes.src import LOGGER_PACKAGE_PATH
from scan_text_recipes.utils.logger.basic_logger import BaseLogger
from scan_text_recipes.utils.utils import read_yaml, load_or_create_instance, remove_special_characters


class BaseDatabaseInterface:
    ...


class DatabaseInterface(BaseDatabaseInterface):

    def __init__(
            self, db_config: Union[str, Dict], db_connect_config: Union[str, Dict], setup_config: Union[str, Dict],
            logger=None, **kwargs
    ):
        self.logger = load_or_create_instance(
            logger, BaseLogger, LOGGER_PACKAGE_PATH, **{**{"name": self.__class__.__name__}, **kwargs}
        )
        self.db_config = db_config if isinstance(db_config, dict) else read_yaml(db_config)
        self.setup_config = setup_config if isinstance(setup_config, dict) else read_yaml(setup_config)
        self.db_connect_config = db_connect_config if isinstance(db_connect_config, dict) else read_yaml(db_connect_config)
        self.connection, self.cursor = self.connect_to_db()

        # drop tables for debug only
        self.drop_tables(self.db_config)
        self.drop_categories()

        self.create_categories()
        self.create_tables(self.db_config)

    def connect_to_db(self) -> Tuple:
        """
        Connects to the database using the provided configuration.
        """
        try:
            conn = psycopg2.connect(
                dbname=os.environ.get('dbname'),
                user=os.environ.get('user'),
                password=os.environ.get('password'),
                host=os.environ.get("DB_HOST"),
                port=os.environ.get('port')
            )
            cur = conn.cursor()
            self.logger.log("Database connection established.")
            return conn, cur
        except Exception as e:
            self.logger.error(f"Error connecting to database: {e}")
            return None, None

    def execute_query(self, query, *args, **kwargs):
        self.cursor.execute(query, *args, **kwargs)
        self.connection.commit()
        if self.cursor.description is not None:
            return self.cursor.fetchall()
        return None

    @staticmethod
    def create_table_sql(table_name, columns: Dict) -> str:
        """
        Generates a CREATE TABLE SQL statement from a dictionary schema.
        """
        column_definitions = ",\n    ".join([f"{col_name} {col_type}" for col_name, col_type in columns.items()])
        return f"CREATE TABLE IF NOT EXISTS {table_name} (\n    {column_definitions}\n);"

    def create_tables(self, schema_config: Dict):
        for table_name in schema_config['TABLES_CREATION_ORDER']:
            table_props = schema_config['RECIPE_DATABASE'][table_name]
            query = self.create_table_sql(table_name, table_props)
            self.logger.info(f"Creating Table: {table_name}")
            self.execute_query(query.replace('"', "'"))

        for _, table_constraints in schema_config['CONSTRAINTS'].items():
            for table_constraint in table_constraints:
                self.execute_query(table_constraint)
        self.logger.log("Tables created successfully!")

    def drop_tables(self, schema_config: Dict):
        for table_name in schema_config['TABLES_CREATION_ORDER']:
            query = f"DROP TABLE IF EXISTS {table_name} CASCADE;"
            self.execute_query(query.replace('"', "'"))

    @staticmethod
    def create_category_sql(category_name: str, category_values: List[str]) -> str:
        return f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{category_name}') THEN
                CREATE TYPE {category_name} AS ENUM {str((*category_values,))};
            END IF;
        END $$;
        """

    def create_categories(self):
        for category_name, category_values in self.db_config['CATEGORIES'].items():
            query = self.create_category_sql(category_name, category_values)
            self.execute_query(query.replace('"', "'"))
            self.logger.info(f"Creating Category: {category_name}")
        self.logger.log("Categories created successfully!")

    def drop_categories(self):
        for enum_name in self.db_config['CATEGORIES']:
            query = f"DROP TYPE IF EXISTS {enum_name} CASCADE;"
            self.execute_query(query.replace('"', "'"))

    def insert_dish(self, description: str, name: str, dish_type: str):
        query = f"""
                INSERT INTO dishes (name, description, category_id) 
                VALUES ('{name}', '{description}', '{dish_type}'::dish_types_enum) 
                ON CONFLICT (name)
                DO UPDATE SET name = EXCLUDED.name
                RETURNING id;
            """
        res = self.execute_query(query)
        return res if res is None else res[0][0]

    def add_ingredient_to_inventory(self, ingredient: Dict, category_id: str, description: str, units: str):
        query = f"""
                INSERT INTO ingredients (name, ingredient_description, category_id, units) 
                VALUES ('{ingredient["name"]}', '{description}', '{category_id}', '{units}') 
                ON CONFLICT (name)
                DO UPDATE SET name = EXCLUDED.name
                RETURNING id;
            """
        res = self.execute_query(query)
        return res if res is None else res[0][0]

    def add_ingredient_to_recipe(self, ingredient: Dict, dish_id: int, ingredient_id: int):
        quantity = np.nan if ingredient['quantity'] is None else ingredient['quantity']
        query = f"""
                INSERT INTO recipe_ingredients (dish_id, ingredient_id, quantity, instructions, intermediate) 
                VALUES ('{dish_id}', '{ingredient_id}', '{quantity}', '{ingredient["instructions"]}', '{ingredient["intermediate"]}') 
                ON CONFLICT (dish_id, ingredient_id, quantity)
                DO NOTHING;
            """
        self.execute_query(query)

    def add_resource_to_kitchen_setup(self, resource: Dict, resource_props: Dict):
        query = f"""
                INSERT INTO resources (name, resource_description, volume, max_temperature) 
                VALUES ('{resource["name"]}', '{resource_props["resource_description"]}', '{resource_props["volume"]}', '{resource_props["max_temperature"]}')
                ON CONFLICT (name)
                DO UPDATE SET name = EXCLUDED.name
                RETURNING id;
            """
        res = self.execute_query(query)
        return res if res is None else res[0][0]

    def add_resource_to_recipe(self, resource: Dict, dish_id, resource_id):
        query = f"""
                INSERT INTO recipe_resources (dish_id, resource_id, usage_time, temperature, occupancy, instructions) 
                VALUES ('{dish_id}', '{resource_id}', '{resource["usage_time"]}', '{resource["temperature"]}', '{resource["occupancy"]}', '{resource["instructions"]}') 
                ON CONFLICT (dish_id, resource_id, usage_time, temperature, occupancy, instructions)
                DO NOTHING;
            """
        self.execute_query(query)

    def add_resource_ingredient_mapping(self, dish_id: int, from_id: int, to_id: int, instructions: str):
        query = f"""
                INSERT INTO resource_ingredient_mapping (dish_id, from_id, to_id, instructions)
                VALUES ('{dish_id}', '{from_id}', '{to_id}', '{instructions}') 
                ON CONFLICT (dish_id, from_id, to_id)
                DO NOTHING;
            """
        self.execute_query(query)

    @staticmethod
    def expand_nested_dict(d: Dict) -> Dict:
        expanded = {}
        for key, value in d.items():
            if isinstance(value, dict):
                for subkey, subval in value.items():
                    expanded[f"{subkey}_{key}"] = subval
            else:
                expanded[key] = value
        return expanded

    def insert_recipe_into_db(self, structured_recipe: Dict, text_recipe: str, dish_name: str):
        # Insert dish into main table
        text_recipe = remove_special_characters(text_recipe)
        default_dish_type = "Main Dish"  # for now
        self.logger.info(f"Adding dish to kitchen setup: {dish_name}")
        dish_id = self.insert_dish(description=text_recipe, name=dish_name, dish_type=default_dish_type)

        # Insert Ingredients
        default_category_id = "Other"
        default_description = ""
        for idx, ingredient in enumerate(structured_recipe["ingredients"]):
            units = "units"
            if ingredient['name'] in self.setup_config['ALLOWED_INGREDIENTS'] and 'quantity' in self.setup_config['ALLOWED_INGREDIENTS'][ingredient['name']]:
                units = self.setup_config['ALLOWED_INGREDIENTS'][ingredient['name']]['quantity']
            self.logger.log(f"Adding ingredient to kitchen setup: {ingredient}")
            ingredient_id = self.add_ingredient_to_inventory(
                ingredient, category_id=default_category_id, units=units,
                description=default_description
            )
            structured_recipe["ingredients"][idx]['ingredient_id'] = ingredient_id
            self.logger.info(f"Adding ingredient to recipe: {ingredient}")
            self.add_ingredient_to_recipe(ingredient, dish_id, ingredient_id)

        # Insert Resources
        for idx, resource in enumerate(structured_recipe["resources"]):
            # TODO: FIX in pre-processing function
            resource_props = dict(resource_description="", volume=10, max_temperature=100)
            self.logger.info(f"Adding resource to kitchen setup: {resource}")
            resource_id = self.add_resource_to_kitchen_setup(resource, resource_props)
            structured_recipe["resources"][idx]["resource_id"] = resource_id
            # TODO: FIX in pre-processing function
            resource["occupancy"] = 1
            resource["temperature"] = np.nan if ("temperature" not in resource or resource["temperature"] is None) else resource["temperature"]
            self.logger.info(f"Adding resource to recipe: {resource}")
            self.add_resource_to_recipe(resource, dish_id, resource_id)

        # Insert resource - ingredient mapping
        for edge in structured_recipe["edges"]:
            self.logger.info(f"Adding resource-ingredient mapping: {edge}")
            self.add_resource_ingredient_mapping(dish_id, edge["from"], edge["to"], edge["instructions"])

        self.logger.log(f"Successfully added dish {dish_name} to recipe")
        return structured_recipe
