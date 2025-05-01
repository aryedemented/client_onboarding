from new_client_integ import LOADER_PACKAGE_PATH, MATCHER_PATH
from new_client_integ.data_loaders.excel_loader import BaseDataLoader
from new_client_integ.matchers.matchers import BaseMatcher
from scan_text_recipes.utils.utils import initialize_pipeline_segments, read_yaml


class FindMatches:

    def __init__(self, cfg):
        self.config = cfg
        self.inventory_data_loader = initialize_pipeline_segments(
            package_path=LOADER_PACKAGE_PATH,
            segment_config=self.config['INVENTORY_DATA_LOADER'],
            class_type=BaseDataLoader,
        )[0]

        self.client_data_loader = initialize_pipeline_segments(
            package_path=LOADER_PACKAGE_PATH,
            segment_config=self.config['CLIENT_DATA_LOADER'],
            class_type=BaseDataLoader,
        )[0]

        self.matcher = initialize_pipeline_segments(
            package_path=MATCHER_PATH,
            segment_config=self.config['MATCHER'],
            class_type=BaseMatcher,
        )[0]

    def find_matches(self, client, inventory):
        # Placeholder for actual duplicate finding logic
        # Load data
        inventory_items_list = self.inventory_data_loader.load(inventory)
        client_items_list = self.client_data_loader.load(client)
        # Preprocess data
        item_pairs = self.matcher.match(client=client_items_list, inventory=inventory_items_list)


if __name__ == '__main__':
    config = read_yaml("D:\\Projects\\Kaufmann_and_Co\\recepies\\scan_code\\ScanRecepies\\new_client_integ\\matcher_config.yaml")
    inventory_file_path = "D:\\Projects\\Kaufmann_and_Co\\ingredients_matching\\inventory.csv"
    client_file_path = "D:\\Projects\\Kaufmann_and_Co\\ingredients_matching\\new_client.csv"

    find_duplicates = FindMatches(cfg=config)
    matched_ingredients, mismatched_ingredients = find_duplicates.find_matches(client=client_file_path, inventory=inventory_file_path)
    for ing1, ing2, score, _, _ in matched_ingredients:
        print(f"{ing1} <-> {ing2}: {score:.2f}")
