from abc import abstractmethod
from typing import List, Dict, Tuple

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from new_client_integ.pre_classifiers.pre_classifier import EmbeddingClassifier
from new_client_integ.utils import clean_text


class BaseRefiner:
    refiner_model = None

    def __init__(self, cfg: Dict):
        self.config = cfg
        self.load_refiner_model()

    @abstractmethod
    def load_refiner_model(self):
        """
        Load the refiner model based on the configuration.
        """
        # Placeholder for actual model loading logic
        pass

    def refine(self, data: List[Tuple[str, str, float, int, int]], emb_dict: Dict = None) -> List[Tuple[str, str, float, int, int]]:
        """
        # Perform some refinement on the data using the model
        refined_data = self.refiner_model.refine(data)
        return refined_data
        """
        # Placeholder for actual refinement logic
        return data


class MinimalSimilarityRefiner(BaseRefiner, EmbeddingClassifier):
    def __init__(self, config: Dict, lemmatization_model=None):
        BaseRefiner.__init__(self, config)
        EmbeddingClassifier.__init__(
            self, config, device='cpu', use_cache=False
        )
        self.apply_lemmatization = True if lemmatization_model else False
        self.lemmatization_model = lemmatization_model

    def load_refiner_model(self):
        """
        Load the refiner model based on the configuration.
        """
        pass

    @staticmethod
    def split_words(phrase: str) -> List[str]:
        """
        Splits the phrase into words.
        """
        return [clean_text(word) for word in phrase.split()]

    def refine(self, data: List[Tuple[str, str, float, int, int]], emb_dict: Dict = None) -> List[Tuple[str, str, float, int, int]]:
        """
        Refine the data based on similarity scores.
        """
        items = []
        for pair in data:
            # Assuming pair is a tuple of (score, ing1, ing2, index1, index2)
            ing1, ing2, _, idx1, idx2 = pair
            inj1_words = self.split_words(ing1)
            inj2_words = self.split_words(ing2)
            new_score = self.gen_score(inj1_words, inj2_words, emb_dict)
            items.append((ing1, ing2, new_score, idx1, idx2))
        # Sort threshold
        items = [item for item in items if item[2] > self.config["THRESHOLD"]]
        return items

    def get_embedding(self, words: List[str], emb_dict: Dict, apply_lemmatization: bool = False) -> np.ndarray:
        """
        Get the embedding for the words using the provided embedding dictionary.
        """
        if emb_dict is None:
            raise ValueError("Embedding dictionary is required.")
        if apply_lemmatization:
            words = [self.refiner_model(word).lemma for word in words]
        return np.array([emb_dict[word] for word in words])

    def gen_score(self, ing1_words: List[str], ing2_words: List[str], emb_dict: Dict = None) -> float:
        """
        Generate a score based on the minimal similarity score of the words in the phrases.
        """
        # Assuming self.similarity_matrix is already computed
        if emb_dict is None:
            embed1 = self.embed_ingredients(tuple(ing1_words))
            embed2 = self.embed_ingredients(tuple(ing2_words))
        else:
            embed1 = self.get_embedding(ing1_words, emb_dict, self.apply_lemmatization)
            embed2 = self.get_embedding(ing2_words, emb_dict, self.apply_lemmatization)

        similarity_matrix = cosine_similarity(embed1, embed2)
        return self.minimal_of_maximal_similarity_full(similarity_matrix)

    @staticmethod
    def minimal_of_maximal_similarity_full(similarity_matrix):
        max_per_row = similarity_matrix.max(axis=1)  # Best match in B for each word in A
        max_per_col = similarity_matrix.max(axis=0)  # Best match in A for each word in B
        return min(max_per_row.min(), max_per_col.min())  # The overall worst matching


if __name__ == '__main__':
    similar_pairs = [
        ('תחתית זהב למוס עגול', 'תחתית למוס עגול', np.float64(0.8397), 2, 46),
        ('עגבניה', 'עגבניה פרוסה', np.float64(0.8262), 3, 76),
        ('מיץ לימון', 'מיץ תפוזים', np.float64(0.848), 16, 151),
        ('כרוב לבן', 'כרוב אדום', np.float64(0.8479), 40, 175),
        ('בזילקום', 'בזיליקום', np.float64(0.9176), 59, 64),
        ('עיגול זהב למוס עגול', 'עיגול זהב למוס', np.float64(0.89823), 77, 99),
        ('פלפל שחור גרוס', 'פלפל אדום', np.float64(0.8005), 96, 214),
        ('עדשים שחורות', 'עדשים אדומות', np.float64(0.8354), 101, 160),
        ("צ'ילי מתוק", "צ'ילי גרוס", np.float64(0.8905), 119, 212),
        ('מוצרלה כדורים גדולים', 'מוצרלה כדורים קטנים',  np.float64(0.9612), 168, 191),
        ("ז'לטין", "ג'לטין", np.float64(0.8279), 206, 222)
    ]

    # Example configuration
    cfg = {
        "trust_description": True,
        "THRESHOLD": 0.8,
        "embedding_params": {"MODEL_NAME": "avichr/heBERT", "PCA": False},
        "refiner_params": {'language': 'he', 'model': 'stanza'}
    }
    refiner = MinimalSimilarityRefiner(cfg)
    similar_pairs = refiner.refine(similar_pairs)
    for ing1, ing2, score, _, _ in similar_pairs:
        print(f"{ing1} <-> {ing2}: {score:.2f}")
