import copy
from typing import Dict, List

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F

from new_client_integ.find_duplicates import FindDuplicates
from new_client_integ.fine_tuning.refiner import MinimalSimilarityRefiner
from new_client_integ.matchers.matchers import CosineSimilarityMatcher
from new_client_integ.pre_classifiers.pre_classifier import EmbeddingClassifier
from new_client_integ.utils import clean_text
from scan_text_recipes.utils.utils import read_yaml


class FindMatches(FindDuplicates):
    _inventory: pd.DataFrame = None
    _inventory_embeddings: Dict = None

    def __init__(self, cfg):
        super().__init__(cfg)
        self.data_loader = None
        self.client_data_loader = None
        self.matcher = None
        self.pre_classifier = None
        self.fine_tuner = None
        self.load_pipeline(self.config)

    def load_pipeline(self, config):
        self.pre_classifier = EmbeddingClassifier(**config["CLASSIFIER_PARAMS"])
        self.matcher = CosineSimilarityMatcher(**config['MATCHER'])
        self.fine_tuner = MinimalSimilarityRefiner(**config["FINE_TUNNER"])

    @property
    def inventory(self):
        return self._inventory if self._inventory is not None else pd.DataFrame()

    @inventory.setter
    def inventory(self, value):
        self._inventory = value

    @property
    def inventory_embeddings(self):
        return self._inventory_embeddings if self._inventory_embeddings is not None else {}

    def find_matches(
            self,
            client_inventory_list: List[str],
    ) -> [pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Compare client inventory to known inventory using cosine similarity.

        Returns a sorted DataFrame:
        | client_item | inventory_match | similarity_score |
        """
        # 🔹 Embed both sets
        emb_inventory = self.pre_classifier.embed_ingredients(tuple(self.inventory['_name']))
        emb_client = self.pre_classifier.embed_ingredients(tuple(client_inventory_list))
        items_list = list(np.unique([*client_inventory_list, *(list(self.inventory['_name']))]))
        words_embeddings_dict = self.create_word_embeddings_dictionary(items_list) \
            if self.config.get("use_word_embeddings", True) else None

        # 🔸 Apply PCA to combined embedding if configured
        if self.config["CLASSIFIER_PARAMS"]['config'].get("PCA", True):
            n_components = self.config["CLASSIFIER_PARAMS"]['config'].get("PCA_COMPONENTS", 50)
            combined = torch.cat([emb_inventory, emb_client], dim=0)
            combined_pca = self.pre_classifier.torch_pca(combined, n_components)
            combined_pca = F.normalize(combined_pca, p=2, dim=1)
            emb_inventory = combined_pca[:len(self.inventory)]
            emb_client = combined_pca[len(self.inventory):]
        else:
            emb_inventory = F.normalize(emb_inventory, p=2, dim=1)
            emb_client = F.normalize(emb_client, p=2, dim=1)

        # 🔸 Compute cosine similarity (cross-match)
        similarity_matrix = torch.matmul(emb_client, emb_inventory.T)  # shape: (N_client, N_inventory)

        results = []
        for i in range(similarity_matrix.size(0)):
            row = similarity_matrix[i].cpu()
            # ✅ Get top-2 indices and scores
            top_scores, top_indices = torch.topk(row, 10)
            max_score = top_scores.max()
            if max_score < self.config["MATCHER"]["threshold"]:
                df = copy.deepcopy(self.inventory.loc[top_indices.numpy(), '_name']).to_frame()
                df['item'] = client_inventory_list[i]
                df['score'] = top_scores.numpy()
                df['idx1'] = i
                df['idx2'] = top_indices.numpy()
                df['new_scores'] = [float(x[2]) for x in self.fine_tuner.get_word_bag_scores(df.values, words_embeddings_dict)]
                top_scores = df[['score', 'new_scores']].max(axis=1).values
                max_score = top_scores.max()

            matches = copy.deepcopy(self.inventory.loc[top_indices, ])
            matches['score'] = top_scores
            matches = matches.sort_values("score", ascending=False).reset_index(drop=True)[:5]
            match_dict = {
                "client_item": client_inventory_list[i],
                "matches": matches,
                "best_score": max_score,
            }
            results.append(match_dict)
        # sort results by best_score
        return sorted(results, key=lambda x: x["best_score"], reverse=True)


if __name__ == '__main__':
    config = read_yaml("D:\\Projects\\Kaufmann_and_Co\\recepies\\scan_code\\ScanRecepies\\new_client_integ\\matcher_config.yaml")
    inventory_file_path = "D:\\Projects\\Kaufmann_and_Co\\ingredients_matching\\RawMaterial-2025-05-04.csv"
    client_file_path = "D:\\Projects\\Kaufmann_and_Co\\ingredients_matching\\nono_items_fixed.csv"

    from new_client_integ.data_loaders.excel_loader import CSVDataLoader, InventoryLoader
    find_matches = FindMatches(cfg=config)
    loader_config = {'filter_by': {}, 'name_column': "name", 'id_column': "id"}
    find_matches.inventory = InventoryLoader(config=loader_config).load(inventory_file_path)
    # loader_config = {'filter_by': {"מוצר בסיס/ חומר גלם": "חומר גלם"}, 'name_column': "שם הרכיב"}
    loader_config = {'filter_by': {}, 'name_column': "ItemName"}
    client_list = CSVDataLoader(loader_config).load(client_file_path)
    matches = find_matches.find_matches(
        client_inventory_list=client_list
    )
    for match in matches:
        print(f"{match['client_item']}:")
        print(match['matches'])
