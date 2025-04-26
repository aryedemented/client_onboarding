from fuzzywuzzy import fuzz
from sklearn.metrics.pairwise import cosine_similarity

from new_client_integ.pre_classifiers.pre_classifier import EmbeddingClassifier


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
                if score >= self.threshold * 100:  # Convert to percentage
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
        client_embeddings = self.embed_ingredients(client)
        inventory_embeddings = self.embed_ingredients(inventory)
        score = cosine_similarity(client_embeddings, inventory_embeddings)
        # TODO: Implement logic to find pairs based on cosine similarity scores

        return matched_items, mismatched_items

    @staticmethod
    def cosine_similarity(item1, item2):
        # Placeholder for actual cosine similarity calculation
        return fuzz.ratio(item1, item2) / 100  # Example using fuzz.ratio as a proxy