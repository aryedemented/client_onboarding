from new_client_integ import LOADER_PACKAGE_PATH, PRE_CLASSIFIERS_PATH, REFINERS_PATH
from new_client_integ.data_loaders.excel_loader import BaseDataLoader
from new_client_integ.fine_tuning.refiner import BaseRefiner
from new_client_integ.pre_classifiers.pre_classifier import BaseClassifier
from scan_text_recipes.utils.utils import initialize_pipeline_segments, read_yaml


class FindDuplicates:
    def __init__(self, cfg):
        self.config = cfg
        self.data_loader = initialize_pipeline_segments(
            package_path=LOADER_PACKAGE_PATH,
            segment_config=self.config['DATA_LOADER'],
            class_type=BaseDataLoader,
        )[0]

        self.pre_classifier = initialize_pipeline_segments(
            package_path=PRE_CLASSIFIERS_PATH,
            segment_config=self.config['PRE_CLASSIFIER'],
            class_type=BaseClassifier,
        )[0]

        self.fine_tuners = initialize_pipeline_segments(
            package_path=REFINERS_PATH,
            segment_config=self.config['REFINERS'] if self.config['REFINERS'] else [],
            class_type=BaseRefiner,
        )

    def find_duplicates(self, filename):
        # Placeholder for actual duplicate finding logic
        # Load data
        items_list = self.data_loader.load(filename)
        # Preprocess data
        item_pairs = self.pre_classifier.classify(items_list)
        # for ing1, ing2, score, _, _ in item_pairs:
        #     print(f"{ing1} <-> {ing2}: {score:.2f}")
        # Fine-tune data
        for fine_tuner in self.fine_tuners:
            item_pairs = fine_tuner.refine(item_pairs)
        for ing1, ing2, score, _, _ in item_pairs:
            print(f"{ing1} <-> {ing2}: {score:.2f}")
        return item_pairs

    def run(self):
        # Placeholder for actual run logic
        pass


if __name__ == '__main__':
    config = read_yaml("/new_client_integ/duplicates_config.yaml")
    file_path = "D:\\Projects\\Kaufmann_and_Co\\ingredients_matching\\new_client.csv"
    find_duplicates = FindDuplicates(cfg=config)
    possible_replacements = find_duplicates.find_duplicates(filename=file_path)
    # for ing1, ing2, score, _, _ in possible_replacements:
    #     print(f"{ing1} <-> {ing2}: {score:.2f}")

