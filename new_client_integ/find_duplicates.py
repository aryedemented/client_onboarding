from typing import Dict

import numpy as np
import pandas as pd
import stanza
import torch

from new_client_integ import LOADER_PACKAGE_PATH, PRE_CLASSIFIERS_PATH, REFINERS_PATH
from new_client_integ.data_loaders.excel_loader import BaseDataLoader
from new_client_integ.fine_tuning.refiner import BaseRefiner
from new_client_integ.pre_classifiers.pre_classifier import BaseClassifier
from new_client_integ.utils import clean_text
from scan_text_recipes.utils.utils import initialize_pipeline_segments, read_yaml


class FindDuplicates:
    lemmatization_model = None
    items_list = None

    def __init__(self, cfg):
        self.config = cfg
        self.data_loader = None
        self.pre_classifier = None
        self.fine_tuners = None
        self.load_pipeline(self.config)

    def load_pipeline(self, config):
        self.data_loader = initialize_pipeline_segments(
            package_path=LOADER_PACKAGE_PATH,
            segment_config=config['DATA_LOADER'],
            class_type=BaseDataLoader,
        )
        if len(self.data_loader) > 0:  # possible to load dataloader later
            self.data_loader = self.data_loader[0]

        self.pre_classifier = initialize_pipeline_segments(
            package_path=PRE_CLASSIFIERS_PATH,
            segment_config=config['PRE_CLASSIFIER'],
            class_type=BaseClassifier,
        )[0]

        self.fine_tuners = initialize_pipeline_segments(
            package_path=REFINERS_PATH,
            segment_config=config['REFINERS'] if config['REFINERS'] else [],
            class_type=BaseRefiner,
        )
        self.load_lemmatization_model()

    def load_lemmatization_model(self):
        apply_lemmatization = self.config.get("lemmatization", {}).get("enabled", False)
        if apply_lemmatization:
            self.lemmatization_model = stanza.Pipeline(lang=self.config['lemmatization']['language'], processors='tokenize,mwt,pos,lemma')

    @staticmethod
    def get_words_list(items_list):
        """
        Given a list of items, returns a list of words.
        """
        words_list = []
        for item in items_list:
            words = [clean_text(itm) for itm in item.split()]
            words_list.extend(words)
        return np.unique(words_list).tolist()

    def create_word_embeddings_dictionary(self, items_list) -> Dict[str, torch.Tensor]:
        """
        Given a list of items, returns a dictionary of words and their embeddings.
        """
        words_list = self.get_words_list(items_list)
        if self.lemmatization_model is not None:
            words_list = [self.lemmatization_model(word).lemma for word in words_list]
        words_embeddings = self.pre_classifier.embed_ingredients(tuple(words_list))
        # apply PCA if needed
        if self.config.get("PCA", True):
            n_components = self.config.get("PCA_COMPONENTS", 50)
            words_embeddings = self.pre_classifier.torch_pca(words_embeddings, n_components)
            words_embeddings = torch.nn.functional.normalize(words_embeddings, p=2, dim=1)
        words_dict = {word: embedding.cpu() for word, embedding in zip(words_list, words_embeddings)}
        return words_dict

    def find_duplicates(self, filename):
        # Placeholder for actual duplicate finding logic
        # Load data
        self.items_list = self.data_loader.load(filename)
        # Preprocess data
        item_pairs = self.pre_classifier.classify(self.items_list)

        # reduce embedding space to words in the items_list
        words_embeddings_dict = self.create_word_embeddings_dictionary(self.items_list) \
            if self.config.get("use_word_embeddings", True) else None

        for fine_tuner in self.fine_tuners:
            item_pairs = fine_tuner.refine(item_pairs, words_embeddings_dict)
        for ing1, ing2, score, _, _ in item_pairs:
            print(f"{ing1} <-> {ing2}: {score:.2f}")
        print("\n" * 5)
        print(f"Total pairs: {len(item_pairs)}")
        return item_pairs

    def set_data_loader(self, data_loader):
        self.data_loader = data_loader

    def get_items_list(self):
        """
        Returns the items list.
        """
        return self.items_list


if __name__ == '__main__':
    config = read_yaml("D:\\Projects\\Kaufmann_and_Co\\recepies\\scan_code\\ScanRecepies\\new_client_integ\\duplicates_config.yaml")
    # file_path = "D:\\Projects\\Kaufmann_and_Co\\ingredients_matching\\new_client.csv"
    file_path = "D:\\Projects\\Kaufmann_and_Co\\ingredients_lists\\חומרי גלם לקוחות פאביוס.csv"
    find_duplicates = FindDuplicates(cfg=config)
    possible_replacements = find_duplicates.find_duplicates(filename=file_path)
    pairs = pd.DataFrame(possible_replacements, columns=["ing1", "ing2", "score", "index1", "index2"])
    pairs.loc[:, ["ing1", "ing2", "score"]].to_csv("D:\\Projects\\Kaufmann_and_Co\\ingredients_lists\\fabios_duplicates_pairs.csv", index=False, encoding='utf-8-sig')
