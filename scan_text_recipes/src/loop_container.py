import copy
from abc import abstractmethod
from typing import Dict, Union, Type, List

from scan_text_recipes.utils.utils import initialize_pipieline_segments


class LoopContainer:
    """
    A class that represents a loop container for processing recipes.
    It initializes the pipeline segments based on the provided configuration and class type.
    The loop iterates through the segments for a specified number of iterations,
    processing the recipe in each iteration.
    """
    def __init__(self, iterations: int, package_path: str, segment_config: List[Dict], class_type: Type, **kwargs):
        self.processors = initialize_pipieline_segments(
            package_path=package_path,
            segment_config=segment_config,
            class_type=class_type,
            **kwargs
        )
        self._iterations = iterations

    @abstractmethod
    def process_recipe(self, *args, **kwargs) -> Union[str, Dict[str, List]]:
        raise NotImplementedError("Subclasses should implement this method.")

    def run_loop(self, recipe: Union[str, Dict]) -> [bool, Union[str, Dict]]:
        tmp_recipe = copy.deepcopy(recipe)
        for i in range(self._iterations):
            res_bool, tmp_recipe = self.process_recipe(tmp_recipe)
            if res_bool:
                break
        return tmp_recipe
