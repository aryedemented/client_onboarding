from abc import abstractmethod
from typing import List, Dict, Tuple

import numpy as np
import stanza
from sklearn.preprocessing import normalize
from sklearn.metrics.pairwise import cosine_similarity

from new_client_integ.pre_classifiers.pre_classifier import EmbeddingClassifier


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

    def refine(self, data: List[Tuple[str, str, float, int, int]]) -> List[Tuple[str, str, float, int, int]]:
        """
        # Perform some refinement on the data using the model
        refined_data = self.refiner_model.refine(data)
        return refined_data
        """
        # Placeholder for actual refinement logic
        return data


class StanzaRefiner(BaseRefiner, EmbeddingClassifier):
    def __init__(self, config: Dict):
        BaseRefiner.__init__(self, config)
        EmbeddingClassifier.__init__(self, config)
        stanza.download(self.config["refiner_params"]['language'])  # First time only

    def load_refiner_model(self):
        """
        Load the refiner model based on the configuration.
        """
        self.refiner_model = stanza.Pipeline(self.config["refiner_params"]['language'])

    def refine(self, data: List[Tuple[str, str, float, int, int]]) -> List[Tuple[str, str, float, int, int]]:
        """
        Reduces given possible pairs list by splitting the phrase on root and secondary parts,
        embedding and comparing both parts separately. Finally, selecting the secondary similarity score
        only if it is higher than the root part
        :param data:
        :return:
        """
        items = []
        for pair in data:
            # Assuming pair is a tuple of (score, ing1, ing2, index1, index2)
            ing1, ing2, _, idx1, idx2 = pair
            ing1_doc = self.refiner_model(ing1)
            inj1_words = self.split_by_head(ing1_doc)
            ing2_doc = self.refiner_model(ing2)
            inj2_words = self.split_by_head(ing2_doc)
            new_score = self.gen_score(inj1_words, inj2_words)
            items.append((ing1, ing2, new_score, idx1, idx2))
        # Sort threshold
        items = [item for item in items if item[2] > self.config["THRESHOLD"]]
        return items

    def gen_score(self, ing1_words: List[str], ing2_words: List[str]) -> float:
        """
        Generate a score based on the similarity of the words in the phrases.
        """
        scores = []
        if ing1_words[0] != ing1_words[0]:
            scores.append(self.embed_ingredients([ing1_words[0], ing2_words[0]]))
        else:
            scores = [1.0]
        if len(ing1_words[1]) > 0 and len(ing2_words[1]) > 0:
            embeddings = self.embed_ingredients([" ".join(ing1_words[1]), " ".join(ing2_words[1])])
            embeddings = normalize(embeddings)
            sim_matrix = cosine_similarity(embeddings)
            scores.append(sim_matrix[0][1])  # similarity between the two phrases
            return scores[1] if scores[1] < scores[0] else scores[0]  # return the minimum score
        else:
            return 1.0  # only one word in the phrase in one of the phrases - let user decide

    @staticmethod
    def split_by_head(phrase) -> [str, List[str]]:
        """
        Splits the phrase by the head word.
        """
        # find root word
        noun = [word.lemma for sent in phrase.sentences for word in sent.words if word.head == 0][0]
        adjs = [word.lemma for sent in phrase.sentences for word in sent.words if word.head > 0]
        return noun, adjs


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
        "THRESHOLD": 0.8,
        "embedding_params": {"MODEL_NAME": "avichr/heBERT", "PCA": False},
        "refiner_params": {'language': 'he', 'model': 'stanza'}
    }
    refiner = StanzaRefiner(cfg)
    similar_pairs = refiner.refine(similar_pairs)
    for ing1, ing2, score, _, _ in similar_pairs:
        print(f"{ing1} <-> {ing2}: {score:.2f}")
