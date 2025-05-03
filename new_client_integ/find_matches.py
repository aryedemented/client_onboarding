from typing import Dict, List

import pandas as pd
import torch
import torch.nn.functional as F

from new_client_integ import LOADER_PACKAGE_PATH, MATCHER_PATH
from new_client_integ.data_loaders.excel_loader import BaseDataLoader
from new_client_integ.find_duplicates import FindDuplicates
from new_client_integ.matchers.matchers import BaseMatcher
from new_client_integ.pre_classifiers.pre_classifier import EmbeddingClassifier
from scan_text_recipes.utils.utils import initialize_pipeline_segments, read_yaml


class FindMatches(FindDuplicates):
    _inventory_list: List = None
    _inventory_embeddings: Dict = None

    def __init__(self, cfg):
        super().__init__(cfg)
        self.data_loader = None
        self.client_data_loader = None
        self.matcher = None
        self.classifier = None
        self.load_pipeline(self.config)

    def load_pipeline(self, config):
        self.classifier = EmbeddingClassifier(**config["CLASSIFIER_PARAMS"])
        self.matcher = initialize_pipeline_segments(
            package_path=MATCHER_PATH,
            segment_config=config['MATCHER'],
            class_type=BaseMatcher,
        )[0]

    @property
    def inventory_list(self):
        return self._inventory_list if self._inventory_list is not None else []

    @inventory_list.setter
    def inventory_list(self, value):
        self._inventory_list = value

    @property
    def inventory_embeddings(self):
        return self._inventory_embeddings if self._inventory_embeddings is not None else {}

    def find_matches(
            self,
            client_inventory_list: List[str],
    ) -> pd.DataFrame:
        """
        Compare client inventory to known inventory using cosine similarity.

        Returns a sorted DataFrame:
        | client_item | inventory_match | similarity_score |
        """
        # 🔹 Embed both sets
        emb_inventory = self.classifier.embed_ingredients(tuple(self.inventory_list))
        emb_client = self.classifier.embed_ingredients(tuple(client_inventory_list))

        # 🔸 Apply PCA to combined embedding if configured
        if self.config["embedding_params"].get("PCA", True):
            n_components = self.config["embedding_params"].get("PCA_COMPONENTS", 50)
            combined = torch.cat([emb_inventory, emb_client], dim=0)
            combined_pca = self.classifier.torch_pca(combined, n_components)
            emb_inventory = combined_pca[:len(self.inventory_list)]
            emb_client = combined_pca[len(self.inventory_list):]

        # 🔹 Normalize embeddings
        emb_inventory = F.normalize(emb_inventory, p=2, dim=1)
        emb_client = F.normalize(emb_client, p=2, dim=1)

        # 🔸 Compute cosine similarity (cross-match)
        similarity_matrix = torch.matmul(emb_client, emb_inventory.T)  # shape: (N_client, N_inventory)

        results = []
        for i in range(similarity_matrix.size(0)):
            row = similarity_matrix[i].cpu()
            max_score = row.max().item()

            # ❌ Skip trivial matches
            if max_score >= 0.9999:
                continue
            # ✅ Get top-2 indices and scores
            top_scores, top_indices = torch.topk(row, 2)
            if max_score < 0.8:
                top_scores, top_indices = None, None
            results.append({
                "client_item": client_inventory_list[i],
                "best_match": self.inventory_list[top_indices[0].item()] if top_scores is not None else None,
                "best_score": round(top_scores[0].item(), 4) if top_scores is not None else None,
                "second_best_match": self.inventory_list[top_indices[1].item()] if top_scores is not None else None,
                "second_score": round(top_scores[1].item(), 4) if top_scores is not None else None,
            })

        df = pd.DataFrame(results)
        return df.sort_values("best_score", ascending=False).reset_index(drop=True)


if __name__ == '__main__':
    config = read_yaml("D:\\Projects\\Kaufmann_and_Co\\recepies\\scan_code\\ScanRecepies\\new_client_integ\\matcher_config.yaml")
    inventory_file_path = "D:\\Projects\\Kaufmann_and_Co\\ingredients_lists\\חומרי גלם לקוחות פאביוס.csv"
    client_file_path = "D:\\Projects\\Kaufmann_and_Co\\ingredients_matching\\new_client_fixed.csv"

    from new_client_integ.data_loaders.excel_loader import CSVListLoader, CSVDataLoader

    find_matches = FindMatches(cfg=config)
    find_matches.inventory_list = CSVListLoader({}).load(inventory_file_path)
    loader_config = {'filter_by': {"מוצר בסיס/ חומר גלם": "חומר גלם"}, 'name_column': "שם הרכיב"}
    client_list = CSVDataLoader(loader_config).load(client_file_path)
    matched_ingredients, mismatched_ingredients = find_matches.find_matches(
        client_inventory_list=client_list
    )
    for ing1, ing2, score, _, _ in matched_ingredients:
        print(f"{ing1} <-> {ing2}: {score:.2f}")
