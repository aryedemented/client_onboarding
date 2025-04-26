from typing import Tuple, List, Dict

import numpy as np
import torch
import torch.nn.functional as F
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize
from transformers import AutoTokenizer, AutoModel


class BaseClassifier:
    def classify(self, items: List[str], **kwargs) -> List[Tuple[str, str]]:
        """
        Given a list of items, returns a list of tuples with similar pairs and their similarity scores.
        Each tuple contains (item1, item2).
        """
        raise NotImplementedError("Subclasses should implement this method.")


class PairCandidateGenerator(BaseClassifier):
    similarity_matrix = None

    def __init__(self, config: Dict = None):
        self.config = config

    @staticmethod
    def get_similar_pairs(sim_matrix, ing_names, threshold=0.8):
        """
        Given a similarity matrix and a threshold, returns a list of tuples with similar pairs and their similarity scores.
        :param sim_matrix:
        :param ing_names:
        :param threshold:
        :return:
        """
        sim_pairs = []

        N = sim_matrix.shape[0]
        for i in range(N):
            for j in range(i + 1, N):  # only upper triangle to avoid duplicates and diagonal
                if sim_matrix[i, j] > threshold:
                    sim_pairs.append((ing_names[i], ing_names[j], sim_matrix[i, j], i, j))
        return sim_pairs

    def classify(self, items: List[str], **kwargs) -> List[Tuple[str, str]]:
        return []


class EmbeddingClassifier(PairCandidateGenerator):
    def __init__(self, config):
        super().__init__(config=config)
        self.embedding_model = None
        self.tokenizer = None
        self.load_embedding_model()

    def load_embedding_model(self):
        """
        Load the embedding model based on the configuration.
        :return:
        """
        if self.embedding_model is None:
            self.tokenizer = AutoTokenizer.from_pretrained(self.config["embedding_params"]["MODEL_NAME"])
            self.embedding_model = AutoModel.from_pretrained(self.config["embedding_params"]["MODEL_NAME"])

    def embed_ingredients(self, items: List[str]) -> torch.Tensor:
        """
        Given a list of items, returns their embeddings.
        :param items:
        :return:
        """
        inputs = self.tokenizer(items, padding=True, truncation=True, return_tensors="pt", max_length=128)
        with torch.no_grad():
            outputs = self.embedding_model(**inputs)
            embeddings = outputs.last_hidden_state
            attention_mask = inputs['attention_mask'].unsqueeze(-1)
            masked_embeddings = embeddings * attention_mask
            summed = masked_embeddings.sum(1)
            counts = attention_mask.sum(1)
            mean_pooled = summed / counts
        return F.normalize(mean_pooled, p=2, dim=1)

    def classify(self, items: List[str], **kwargs) -> List[Tuple[str, str, float, int, int]]:
        """
        Given a list of items, returns a list of tuples with similar pairs and their similarity scores.
        Each tuple contains (item1, item2, score, index1, index2).
        which are item1 name, item2 name, match score, item index1, item index2
        """
        embeddings = self.embed_ingredients(items)
        if self.config["embedding_params"].get("PCA", True):
            pca = PCA(n_components=self.config["embedding_params"].get("PCA_COMPONENTS", 50))
            reduced = pca.fit_transform(embeddings)
            embeddings = normalize(reduced)
        self.similarity_matrix = cosine_similarity(embeddings)
        np.fill_diagonal(self.similarity_matrix, 0)
        sim_pairs = self.get_similar_pairs(self.similarity_matrix, items, threshold=self.config["THRESHOLD"])
        return sim_pairs


if __name__ == '__main__':
    cfg = {
        "THRESHOLD": 0.8,
        "embedding_params": {"MODEL_NAME": "avichr/heBERT", "PCA": True}
    }
    # get items from a CSV file
    import pandas as pd

    filename = "D:\\Projects\\Kaufmann_and_Co\\ingredients_matching\\new_client.csv"
    df = pd.read_csv(filename)
    df = df.loc[:, ~df.columns.str.startswith("Unnamed:")]
    ingredients = df.loc[df['מוצר בסיס/ חומר גלם'] == 'חומר גלם', 'שם הרכיב']
    items_list = list(ingredients.unique())
    items_list = [item.strip() for item in items_list]

    # keep unique items
    items_list = list(set(items_list))

    classifier = EmbeddingClassifier(cfg)
    similar_pairs = classifier.classify(items_list)
    for ing1, ing2, score, _, _ in similar_pairs:
        print(f"{ing1} <-> {ing2}: {score:.2f}")
