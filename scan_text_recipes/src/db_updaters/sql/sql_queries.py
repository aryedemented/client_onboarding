import os
import re
from typing import Dict, List
from scan_text_recipes import PROJECT_ROOT
from scan_text_recipes.utils.utils import execute_query, get_connection, read_config, read_yaml, read_schema_config, \
    read_text


# Database configuration
def create_table_sql(table_name, columns: Dict) -> str:
    """
    Generates a CREATE TABLE SQL statement from a dictionary schema.
    """
    column_definitions = ",\n    ".join([f"{col_name} {col_type}" for col_name, col_type in columns.items()])
    return f"CREATE TABLE IF NOT EXISTS {table_name} (\n    {column_definitions}\n);"


def create_tables(conn, cur, schema_config: Dict):
    for table_name in schema_config['TABLES_CREATION_ORDER']:
        table_props = schema_config['RECIPE_DATABASE'][table_name]
        query = create_table_sql(table_name, table_props)
        print(f"Creating Table: {table_name}")
        execute_query(conn, cur, query.replace('"', "'"))

    for _, table_constraints in schema_config['CONSTRAINTS'].items():
        for table_constraint in table_constraints:
            execute_query(conn, cur, table_constraint)
    print("Tables created successfully!")


def drop_tables(conn, cur, schema_config: Dict):
    for table_name in schema_config['TABLES_CREATION_ORDER']:
        query = f"DROP TABLE IF EXISTS {table_name} CASCADE;"
        execute_query(conn, cur, query.replace('"', "'"))


def create_category_sql(category_name: str, category_values: List[str]) -> str:
    return f"""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{category_name}') THEN
            CREATE TYPE {category_name} AS ENUM {str((*category_values,))};
        END IF;
    END $$;
    """


def create_categories(conn, cur, schema_config: Dict):
    for category_name, category_values in schema_config['CATEGORIES'].items():
        query = create_category_sql(category_name, category_values)
        execute_query(conn, cur, query.replace('"', "'"))
        print(f"Creating Category: {category_name}")
    print("Categories created successfully!")


def drop_categories(conn, cur, schema_config: Dict):
    for enum_name in schema_config['CATEGORIES']:
        query = f"DROP TYPE IF EXISTS {enum_name} CASCADE;"
        execute_query(conn, cur, query.replace('"', "'"))


def insert_dish(conn, cur, description: str, name: str, dish_type: str):
    query = f"""
            INSERT INTO dishes (name, description, category_id) 
            VALUES ('{name}', '{description}', '{dish_type}'::dish_types_enum) 
            ON CONFLICT (name)
            DO UPDATE SET name = EXCLUDED.name
            RETURNING id;
        """
    res = execute_query(conn, cur, query)
    return res if res is None else res[0][0]


def add_ingredient_to_inventory(conn, cur, ingredient: Dict, category_id: str, units: str, description: str):
    query = f"""
            INSERT INTO ingredients (name, ingredient_description, category_id, units) 
            VALUES ('{ingredient["name"]}', '{description}', '{category_id}', '{units}') 
            ON CONFLICT (name)
            DO UPDATE SET name = EXCLUDED.name
            RETURNING id;
        """
    res = execute_query(conn, cur, query)
    return res if res is None else res[0][0]


def add_ingredient_to_recipe(conn, cur, ingredient: Dict, dish_id: int, indredient_id: int):
    query = f"""
            INSERT INTO recipe_ingredients (dish_id, ingredient_id, quantity, instructions) 
            VALUES ('{dish_id}', '{indredient_id}', '{ingredient["quantity"]}', '{ingredient["remarks"]}') 
            ON CONFLICT (dish_id, ingredient_id, quantity)
            DO NOTHING;
        """
    execute_query(conn, cur, query)


def add_resource_to_kitchen_setup(conn, cur, resource: Dict, resource_props: Dict):
    query = f"""
            INSERT INTO resources (name, resource_description, volume, max_temperature, capacity_units) 
            VALUES ('{resource["name"]}', '{resource_props["resource_description"]}', {resource_props["max_temperature"]}, {resource_props["volume"]}, '{resource_props["capacity_units"]}') 
            ON CONFLICT (name)
            DO UPDATE SET name = EXCLUDED.name
            RETURNING id;
        """
    res = execute_query(conn, cur, query)
    return res if res is None else res[0][0]


def add_resource_to_recipe(conn, cur, resource: Dict, dish_id, resource_id):
    query = f"""
            INSERT INTO recipe_resources (dish_id, resource_id, preparation_time, temperature, occupancy, instructions) 
            VALUES ('{dish_id}', '{resource_id}', '{resource["preparation_time"]}', '{resource["temperature"]}', '{resource["occupancy"]}', '{resource["remarks"]}') 
            ON CONFLICT (dish_id, resource_id, preparation_time, temperature, occupancy, instructions)
            DO NOTHING;
        """
    execute_query(conn, cur, query)


def add_resource_ingredient_mapping(conn, cur, dish_id: int, from_node: int, from_id: int, to_node: int, to_id: int, instructions: str):
    query = f"""
            INSERT INTO resource_ingredient_mapping (dish_id, from_node, from_id, to_node, to_id, instructions)
            VALUES ('{dish_id}', '{from_node}', '{from_id}', '{to_node}', '{to_id}', '{instructions}') 
            ON CONFLICT (dish_id, from_node, from_id, to_node, to_id, instructions)
            DO NOTHING;
        """
    execute_query(conn, cur, query)


def insert_dish_into_db(conn, cur, structured_recipe: Dict, text_recipe: str, dish_name: str):
    # Insert dish into main table
    default_dish_type = "Main Dish"  # for now
    dish_id = insert_dish(conn, cur, description=text_recipe, name=dish_name, dish_type=default_dish_type)

    # Insert Ingredients
    default_category_id = "Other"
    default_units = 'gr'
    default_description = ""
    for idx, ingredient in enumerate(structured_recipe["ingredients"]):
        ingredient_id = add_ingredient_to_inventory(
            conn, cur, ingredient,category_id=default_category_id, units=default_units, description=default_description
        )
        structured_recipe["ingredients"][idx]['ingredient_id'] = ingredient_id
        # TODO: FIX IN In pre-processing function
        quantity = re.findall(r'\d+\.?\d*', ingredient['quantity'])
        ingredient['quantity'] = quantity[0] if len(quantity) else 1
        add_ingredient_to_recipe(conn, cur, ingredient, dish_id, ingredient_id)

    # Insert Resources
    for idx, resource in enumerate(structured_recipe["resources"]):
        # TODO: FIX in pre-processing function
        resource_props = dict(resource_description="", volume=10, capacity_units=default_units, max_temperature=100)
        resource_id = add_resource_to_kitchen_setup(conn, cur, resource, resource_props)
        structured_recipe["resources"][idx]["resource_id"] = resource_id
        # TODO: FIX in pre-processing function
        preparation_time = re.findall(r'\d+\.?\d*', resource["preparation_time"])
        resource["preparation_time"] = preparation_time[0] if len(preparation_time) else 10
        resource["temperature"] = 10
        resource["occupancy"] = 1
        add_resource_to_recipe(conn, cur, resource, dish_id, resource_id)

    # Insert resource - ingredient mapping
    for edge in structured_recipe["edges"]:
        # TODO: fix later in correct code:
        from_resource_id = [res['resource_id'] for res in structured_recipe['resources'] if res['name'] == edge['from']]
        from_ingredient_id = [ing['ingredient_id'] for ing in structured_recipe['ingredients'] if ing['name'] == edge['from']]
        if len(from_resource_id):
            from_node = "resource"
            from_id = from_resource_id[0]
        elif len(from_ingredient_id):
            from_node = "ingredient"
            from_id = from_ingredient_id[0]
        else:
            # TODO: FIX treatnemt - should not get here
            continue

        from_resource_id = [res['resource_id'] for res in structured_recipe['resources'] if res['name'] == edge['to']]
        from_ingredient_id = [ing['ingredient_id'] for ing in structured_recipe['ingredients'] if ing['name'] == edge['to']]
        if len(from_resource_id):
            to_node = "resource"
            to_id = from_resource_id[0]
        elif len(from_ingredient_id):
            to_node = "ingredient"
            to_id = from_ingredient_id[0]
        else:
            # TODO: FIX treatnemt - should not get here
            continue

        add_resource_ingredient_mapping(conn, cur, dish_id, from_node, from_id, to_node, to_id, edge["instructions"])

    print(f"Successfully added dish {dish_name} to recipe")
    return structured_recipe


if __name__ == '__main__':
    db_config = read_config()
    connection = get_connection(db_config.DB_CONNECT_PARAMS)
    cursor = connection.cursor()
    db_schema = read_schema_config()

    drop_categories(connection, cursor, db_schema)
    create_categories(connection, cursor, db_schema)

    drop_tables(connection, cursor, db_schema)
    create_tables(connection, cursor, db_schema)

    categories = db_schema["CATEGORIES"]
    dish_name = "Classical Pancakes"
    dish_filename = "classic_pancakes"
    text_recipe = read_text(os.path.join(PROJECT_ROOT, "..", "recipes", f"{dish_filename}.txt"))
    structured_recipe = read_yaml(os.path.join(PROJECT_ROOT, "..", "structured_recipes", f"{dish_filename}.yaml"))

    insert_dish_into_db(connection, cursor, structured_recipe, text_recipe=text_recipe, dish_name=dish_name)
