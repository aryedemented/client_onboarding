import copy
from typing import Union, Dict, List

import torch
from sklearn.metrics.pairwise import cosine_similarity
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel

from scan_text_recipes.src.postprocessors.post_processors import PostProcessor
from scan_text_recipes.tests.examples_for_tests import load_test_setup_config, load_structured_test_recipe
from scan_text_recipes.utils.logger.basic_logger import Logger
from scan_text_recipes.utils.utils import read_yaml, replace_all_occurrences


class NameCorrector(PostProcessor):
    def __init__(
            self, setup_config: Union[str, Dict],
            section_name: str, section_key: str,
            **kwargs
    ):
        super().__init__(**kwargs)
        self.threshold = kwargs.get('threshold', 0.5)
        self.section_name = section_name
        self.setup_config = setup_config if isinstance(setup_config, dict) else read_yaml(setup_config)

        # Loading embedding model
        # TODO: move all the model loading to the embedding model interface
        self.tokenizer = AutoTokenizer.from_pretrained("avichr/heBERT")
        self.model = AutoModel.from_pretrained("avichr/heBERT")
        self.model.eval()
        self.items_list = list(self.setup_config.get(section_key).keys())
        self.section_key = section_key
        self.embeddings = self._embed_sentences(self.items_list)

    def _embed_sentences(self, sentences: list[str]) -> torch.Tensor:
        inputs = self.tokenizer(
            sentences,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=128
        )

        with torch.no_grad():
            outputs = self.model(**inputs)
            embeddings = outputs.last_hidden_state
            attention_mask = inputs['attention_mask'].unsqueeze(-1)
            masked_embeddings = embeddings * attention_mask
            summed = masked_embeddings.sum(1)
            counts = attention_mask.sum(1)
            mean_pooled = summed / counts
            return F.normalize(mean_pooled, p=2, dim=1)  # normalize for cosine similarity

    def find_best_match(self, query: str) -> tuple[str, float]:
        """
        Given a query string, returns the best match from the original list and its similarity score.
        """
        query_embedding = self._embed_sentences([query])
        scores = cosine_similarity(query_embedding, self.embeddings)[0]
        best_idx = scores.argmax()
        return self.items_list[best_idx], scores[best_idx].item()

    def process_recipe(self, recipe_dict: Dict[str, List], recipe_text: str, **kwargs) -> [bool, Dict[str, List]]:
        section = copy.deepcopy(recipe_dict[self.section_name])
        replacements = {}
        for item_idx, item in enumerate(section):
            item_name = item.get("name")
            if item_name in self.items_list or item_name == self.setup_config["FINAL_NODE_NAME"]:
                continue
            best_match, score = self.find_best_match(item_name)
            if best_match:
                if section[item_idx]["name"] != best_match:
                    self.logger.warning(f'Replacing: "{section[item_idx]["name"]}" => "{best_match}"')
                    replacements[section[item_idx]["name"]] = best_match

        recipe_dict = replace_all_occurrences(data=recipe_dict, replacement_dict=replacements)
        return True, recipe_dict


class IngredientsNamesCorrector(NameCorrector):
    """
    Corrects ingredient names in the recipe.
    """
    def __init__(self, setup_config: Union[str, Dict], **kwargs):
        super().__init__(
            setup_config, section_key='ALLOWED_INGREDIENTS', section_name='ingredients', **kwargs
        )


class ResourcesNamesCorrector(NameCorrector):
    """
    Corrects ingredient names in the recipe.
    """
    def __init__(self, setup_config: Union[str, Dict], **kwargs):
        super().__init__(
            setup_config, section_key='ALLOWED_RESOURCES', section_name='resources', **kwargs
        )


if __name__ == '__main__':
    names_corrector = IngredientsNamesCorrector(setup_config=load_test_setup_config(), logger=Logger(name="Test"))
    # Example usage:
    # structured_recipe = load_structured_test_recipe()
    structured_recipe = read_yaml("D:\\Projects\\Kaufmann_and_Co\\recepies\\scan_code\\ScanRecepies\\structured_recipes\\bruschetta.yaml")
    fixed_names_recipe = names_corrector.process_recipe(
        recipe_dict=structured_recipe,
        recipe_text=""  # not used here
    )
    print(fixed_names_recipe)
