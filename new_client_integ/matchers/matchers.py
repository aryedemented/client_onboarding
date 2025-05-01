import numpy as np
import pandas as pd
from fuzzywuzzy import fuzz
from sklearn.metrics.pairwise import cosine_similarity

from new_client_integ.pre_classifiers.pre_classifier import EmbeddingClassifier
from new_client_integ.utils import clean_text


class BaseMatcher:
    def __init__(self, name):
        self.name = name

    def match(self, client, inventory):
        raise NotImplementedError("Subclasses should implement this method.")


class ExactMatcher(BaseMatcher):
    def __init__(self):
        super().__init__("ExactMatcher")

    def match(self, client, inventory):
        matched_items = []
        mismatched_items = []

        for client_item in client:
            found_match = False
            for inventory_item in inventory:
                if client_item == inventory_item:
                    matched_items.append((client_item, inventory_item))
                    found_match = True
                    break
            if not found_match:
                mismatched_items.append(client_item)

        return matched_items, mismatched_items


class FuzzyMatcher(BaseMatcher):
    def __init__(self, threshold=0.8):
        super().__init__("FuzzyMatcher")
        self.threshold = threshold

    def match(self, client, inventory):
        matched_items = []
        mismatched_items = []

        for client_item in client:
            found_match = False
            for inventory_item in inventory:
                score = fuzz.ratio(client_item, inventory_item)
                if score >= self.threshold:  # Convert to percentage
                    matched_items.append((client_item, inventory_item, score))
                    found_match = True
                    break
            if not found_match:
                mismatched_items.append(client_item)

        return matched_items, mismatched_items


class CosineSimilarityMatcher(BaseMatcher, EmbeddingClassifier):
    def __init__(self, threshold=0.8):
        super().__init__("CosineSimilarityMatcher")
        self.threshold = threshold

    def match(self, client, inventory):
        matched_items = []
        mismatched_items = []
        client_embeddings = self.embed_ingredients(tuple(client))
        inventory_embeddings = self.embed_ingredients(tuple(inventory))
        score = cosine_similarity(client_embeddings, inventory_embeddings)
        # TODO: Implement logic to find pairs based on cosine similarity scores

        return matched_items, mismatched_items


if __name__ == '__main__':
    client_items = ["ingredient1", "ingredient2", "ingredient3"]
    inventory_items = pd.read_csv("D:\\Projects\\Kaufmann_and_Co\\ingredients_lists\\חומרי גלם לקוחות פאביוס.csv", index_col=False)
    inventory_items = inventory_items.T.iloc[0]
    inventory_items = [clean_text(item) for item in list(inventory_items)]
    inventory_items = np.unique(inventory_items).tolist()
    exact_matcher = ExactMatcher()
    # fuzzy_matcher = FuzzyMatcher(threshold=80)
    cosine_matcher = CosineSimilarityMatcher(threshold=0.8)

    exact_matches, exact_mismatches = exact_matcher.match(client_items, inventory_items)
    # fuzzy_matches, fuzzy_mismatches = fuzzy_matcher.match(client_items, inventory_items)
    cosine_matches, cosine_mismatches = cosine_matcher.match(client_items, inventory_items)

    print("Exact Matches:", exact_matches)
    # print("Fuzzy Matches:", fuzzy_matches)
    print("Cosine Matches:", cosine_matches)
