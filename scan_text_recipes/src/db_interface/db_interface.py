import re
from typing import Dict, Tuple, List, Union

import psycopg2

from scan_text_recipes.src import LOGGER_PACKAGE_PATH
from scan_text_recipes.utils.logger.basic_logger import BaseLogger
from scan_text_recipes.utils.utils import read_yaml, load_or_create_instance


class BaseDatabaseInterface:
    ...


class DatabaseInterface(BaseDatabaseInterface):

    def __init__(self, db_config: Union[str, Dict], db_connect_config: Union[str, Dict], logger=None, **kwargs):
        self.logger = load_or_create_instance(
            logger, BaseLogger, LOGGER_PACKAGE_PATH, **{**{"name": self.__class__.__name__}, **kwargs}
        )
        self.db_config = db_config if isinstance(db_config, dict) else read_yaml(db_config)
        self.db_connect_config = db_connect_config if isinstance(db_connect_config, dict) else read_yaml(db_connect_config)
        self.connection, self.cursor = self.connect_to_db()

    def connect_to_db(self) -> Tuple:
        """
        Connects to the database using the provided configuration.
        """
        try:
            connect_params = self.db_connect_config['DB_CONNECT_PARAMS']
            conn = psycopg2.connect(
                dbname=connect_params['dbname'],
                user=connect_params['user'],
                password=connect_params['password'],
                host=connect_params['host'],
                port=connect_params['port']
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
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typename = '{category_name}') THEN
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

    def add_ingredient_to_inventory(self, ingredient: Dict, category_id: str, units: str, description: str):
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
        query = f"""
                INSERT INTO recipe_ingredients (dish_id, ingredient_id, quantity, instructions) 
                VALUES ('{dish_id}', '{ingredient_id}', '{ingredient["quantity"]}', '{ingredient["remarks"]}') 
                ON CONFLICT (dish_id, ingredient_id, quantity)
                DO NOTHING;
            """
        self.execute_query(query)

    def add_resource_to_kitchen_setup(self, resource: Dict, resource_props: Dict):
        query = f"""
                INSERT INTO resources (name, resource_description, volume, max_temperature, capacity_units) 
                VALUES ('{resource["name"]}', '{resource_props["resource_description"]}', {resource_props["max_temperature"]}, {resource_props["volume"]}, '{resource_props["capacity_units"]}') 
                ON CONFLICT (name)
                DO UPDATE SET name = EXCLUDED.name
                RETURNING id;
            """
        res = self.execute_query(query)
        return res if res is None else res[0][0]

    def add_resource_to_recipe(self, resource: Dict, dish_id, resource_id):
        query = f"""
                INSERT INTO recipe_resources (dish_id, resource_id, usage_time, temperature, occupancy, instructions) 
                VALUES ('{dish_id}', '{resource_id}', '{resource["usage_time"]}', '{resource["temperature"]}', '{resource["occupancy"]}', '{resource["remarks"]}') 
                ON CONFLICT (dish_id, resource_id, usage_time, temperature, occupancy, instructions)
                DO NOTHING;
            """
        self.execute_query(query)

    def add_resource_ingredient_mapping(self, dish_id: int, from_node: str, from_id: int, to_node: str, to_id: int,
                                        instructions: str):
        query = f"""
                INSERT INTO resource_ingredient_mapping (dish_id, from_node, from_id, to_node, to_id, instructions)
                VALUES ('{dish_id}', '{from_node}', '{from_id}', '{to_node}', '{to_id}', '{instructions}') 
                ON CONFLICT (dish_id, from_node, from_id, to_node, to_id, instructions)
                DO NOTHING;
            """
        self.execute_query(query)

    def insert_dish_into_db(self, structured_recipe: Dict, text_recipe: str, dish_name: str):
        # Insert dish into main table
        default_dish_type = "Main Dish"  # for now
        dish_id = self.insert_dish(description=text_recipe, name=dish_name, dish_type=default_dish_type)

        # Insert Ingredients
        default_category_id = "Other"
        default_units = 'gr'
        default_description = ""
        for idx, ingredient in enumerate(structured_recipe["ingredients"]):
            ingredient_id = self.add_ingredient_to_inventory(
                ingredient, category_id=default_category_id, units=default_units,
                description=default_description
            )
            structured_recipe["ingredients"][idx]['ingredient_id'] = ingredient_id
            # TODO: FIX IN In pre-processing function
            quantity = re.findall(r'\d+\.?\d*', ingredient['quantity'])
            ingredient['quantity'] = quantity[0] if len(quantity) else 1
            self.add_ingredient_to_recipe(ingredient, dish_id, ingredient_id)

        # Insert Resources
        for idx, resource in enumerate(structured_recipe["resources"]):
            # TODO: FIX in pre-processing function
            resource_props = dict(resource_description="", volume=10, capacity_units=default_units, max_temperature=100)
            resource_id = self.add_resource_to_kitchen_setup(resource, resource_props)
            structured_recipe["resources"][idx]["resource_id"] = resource_id
            # TODO: FIX in pre-processing function
            usage_time = re.findall(r'\d+\.?\d*', resource["usage_time"])
            resource["usage_time"] = usage_time[0] if len(usage_time) else 10
            resource["temperature"] = 10
            resource["occupancy"] = 1
            self.add_resource_to_recipe(resource, dish_id, resource_id)

        # Insert resource - ingredient mapping
        for edge in structured_recipe["edges"]:
            # TODO: fix later in correct code:
            from_resource_id = [res['resource_id'] for res in structured_recipe['resources'] if
                                res['name'] == edge['from']]
            from_ingredient_id = [ing['ingredient_id'] for ing in structured_recipe['ingredients'] if
                                  ing['name'] == edge['from']]
            if len(from_resource_id):
                from_node = "resource"
                from_id = from_resource_id[0]
            elif len(from_ingredient_id):
                from_node = "ingredient"
                from_id = from_ingredient_id[0]
            else:
                # TODO: FIX treatment - should not get here
                continue

            from_resource_id = [res['resource_id'] for res in structured_recipe['resources'] if
                                res['name'] == edge['to']]
            from_ingredient_id = [ing['ingredient_id'] for ing in structured_recipe['ingredients'] if
                                  ing['name'] == edge['to']]
            if len(from_resource_id):
                to_node = "resource"
                to_id = from_resource_id[0]
            elif len(from_ingredient_id):
                to_node = "ingredient"
                to_id = from_ingredient_id[0]
            else:
                # TODO: FIX treatment - should not get here
                continue

            self.add_resource_ingredient_mapping(dish_id, from_node, from_id, to_node, to_id, edge["instructions"])

        self.logger.log(f"Successfully added dish {dish_name} to recipe")
        return structured_recipe
