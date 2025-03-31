from typing import Union, Dict, List

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from scan_text_recipes.src.postprocessors.post_processors import PostProcessor
from scan_text_recipes.tests.examples_for_tests import load_test_setup_config
from scan_text_recipes.utils.utils import read_yaml


class NameCorrector(PostProcessor):
    def __init__(self, setup_config: Union[str, Dict], section_name: str, **kwargs):
        super().__init__(**kwargs)
        self.section_name = section_name
        self.setup_config = setup_config if isinstance(setup_config, dict) else read_yaml(setup_config)
        # Load a multilingual embedding model (good for Hebrew)
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.items_list = [self.setup_config.get(self.section_name).keys()]
        # Encode the known list once
        self.items_embeddings = self.model.encode(self.items_list)

    def find_closest_match(self, query_term, threshold=0.85):
        query_embedding = self.model.encode([query_term])
        similarities = cosine_similarity(query_embedding, self.items_embeddings)[0]

        best_idx = int(np.argmax(similarities))
        best_score = similarities[best_idx]
        best_match = self.items_list[best_idx]

        if best_score >= threshold:
            return best_match, best_score
        else:
            return None, best_score  # or return the original term as fallback

    def process_recipe(self, recipe_dict: Dict[str, List], recipe_text: str, **kwargs) -> [bool, Dict[str, List]]:
        pass


class IngredientCorrector(NameCorrector):
    """
    Corrects ingredient names in the recipe.
    """
    def __init__(self, setup_config: Union[str, Dict], **kwargs):
        super().__init__(setup_config, section_name='ingredients', **kwargs)


if __name__ == '__main__':

    names_corrector = IngredientCorrector(setup_config=load_test_setup_config(), section_name='ingredients')
    # Example usage:
    query_terms = ["בזיליקום טרי", "תבנית פיצה", "שמן זית", "מחבת גדולה"]

    for term in query_terms:
        match, score = names_corrector.process_recipe(term)
        print(f"Query: {term} → Match: {match} (Score: {score:.2f})")


