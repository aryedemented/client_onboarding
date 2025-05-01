from typing import Tuple, List, Dict

import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel

from new_client_integ.utils import conditional_cache


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
    def get_similar_pairs(sim_matrix: torch.Tensor, ing_names: List[str], threshold=0.8):
        """
        GPU-optimized: Given a similarity matrix and a threshold,
        returns a list of tuples with similar pairs and their similarity scores.
        """
        # Step 1: Create mask of where similarity is above threshold
        mask = (sim_matrix > threshold)

        # Step 2: Only take upper triangle (no duplicate pairs, no self-matches)
        triu_mask = torch.triu(mask, diagonal=1)  # Only take upper triangle without diagonal

        # Step 3: Find (i, j) indices where condition is met
        idx_i, idx_j = torch.nonzero(triu_mask, as_tuple=True)

        # Step 4: Gather the corresponding similarity scores
        scores = sim_matrix[idx_i, idx_j]

        # Step 5: Build the list
        sim_pairs = []
        for k in range(len(scores)):
            i = int(idx_i[k])
            j = int(idx_j[k])
            sim_pairs.append((ing_names[i], ing_names[j], float(scores[k]), i, j))

        return sim_pairs

    def classify(self, items: List[str], **kwargs) -> List[Tuple[str, str]]:
        return []


class EmbeddingClassifier(PairCandidateGenerator):
    def __init__(self, config, device: str = 'cuda', use_cache: bool = True):
        super().__init__(config=config)
        self.device = 'cuda' if torch.cuda.is_available() and device == 'cuda' else 'cpu'
        self.embedding_model = None
        self.tokenizer = None
        self._use_cache = use_cache
        self.load_embedding_model()

    def load_embedding_model(self):
        """
        Load the embedding model based on the configuration.
        :return:
        """
        if self.embedding_model is None:
            self.tokenizer = AutoTokenizer.from_pretrained(self.config["embedding_params"]["MODEL_NAME"])
            self.embedding_model = AutoModel.from_pretrained(self.config["embedding_params"]["MODEL_NAME"])
            print(f"{self.__class__.__name__}: Using device: ", self.device)
            self.embedding_model = self.embedding_model.to(self.device)

    def embed_ingredients(self, items: Tuple[str]) -> torch.Tensor:
        """
        Given a list of items, returns their embeddings.
        """
        if self._use_cache:
            return self._cached_embed_ingredients(items)
        else:
            return self._unchached_embed_ingredients(items)

    @conditional_cache(maxsize=3)
    def _cached_embed_ingredients(self, items: Tuple[str]) -> torch.Tensor:
        return self._embed_ingredients(items)

    def _unchached_embed_ingredients(self, items: Tuple[str]) -> torch.Tensor:
        return self._embed_ingredients(items)

    def _embed_ingredients(self, items: Tuple[str]) -> torch.Tensor:
        """
        Given a list of items, returns their embeddings.
        """
        inputs = self.tokenizer(items, padding=True, truncation=True, return_tensors="pt", max_length=128)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}  # move tokenized inputs to model's device
        with torch.no_grad():
            outputs = self.embedding_model(**inputs)
            embeddings = outputs.last_hidden_state
            attention_mask = inputs['attention_mask'].unsqueeze(-1)
            masked_embeddings = embeddings * attention_mask
            summed = masked_embeddings.sum(1)
            counts = attention_mask.sum(1)
            mean_pooled = summed / counts
        return F.normalize(mean_pooled, p=2, dim=1)

    @staticmethod
    def torch_pca(in_tnsor: torch.Tensor, n_components: int):
        """
        Fast PCA on GPU using PyTorch SVD.
        X: Tensor of shape (n_samples, n_features)
        """
        X_mean = in_tnsor.mean(dim=0, keepdim=True)
        print(f"X_mean on: {X_mean.device}")
        X_centered = in_tnsor - X_mean
        U, S, Vh = torch.linalg.svd(X_centered, full_matrices=False)
        return torch.matmul(X_centered, Vh[:n_components].T)

    def classify(self, items: List[str], **kwargs) -> List[Tuple[str, str, float, int, int]]:
        """
        Given a list of items, returns a list of tuples with similar pairs and their similarity scores.
        Each tuple contains (item1, item2, score, index1, index2)
        """
        embeddings = self.embed_ingredients(tuple(items))  # normalized embeddings on GPU

        # Optionally apply PCA
        if self.config["embedding_params"].get("PCA", True):
            n_components = self.config["embedding_params"].get("PCA_COMPONENTS", 50)
            embeddings = self.torch_pca(embeddings, n_components)
            print(f"embeddings post-pca on: {embeddings.device}")
            embeddings = F.normalize(embeddings, p=2, dim=1)
            print(f"embeddings post-normalization on: {embeddings.device}")

        # Compute full cosine similarity matrix on GPU
        similarity_matrix = torch.matmul(embeddings, embeddings.T)  # (N, D) @ (D, N) = (N, N)
        print(f"similarity_matrix on: {similarity_matrix.device}")

        # Fill diagonal with 0 (so an item won't match itself)
        similarity_matrix.fill_diagonal_(0)

        sim_pairs = self.get_similar_pairs(similarity_matrix, items, threshold=self.config["THRESHOLD"])
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
