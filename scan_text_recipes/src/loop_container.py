import copy
from abc import abstractmethod
from typing import Dict, Union, Type, List
from scan_text_recipes.utils.utils import initialize_pipeline_segments


class LoopContainer:
    """
    A class that represents a loop container for processing recipes.
    It initializes the pipeline segments based on the provided configuration and class type.
    The loop iterates through the segments for a specified number of iterations,
    processing the recipe in each iteration.
    """
    def __init__(self, iterations: int, package_path: str, segment_config: List[Dict], class_type: Type, **kwargs):
        self.processors = initialize_pipeline_segments(
            package_path=package_path,
            segment_config=segment_config,
            class_type=class_type,
            **kwargs
        )
        self._iterations = iterations
        self.recipe = None
        self._logger = kwargs.get("logger")

    @abstractmethod
    def _run_loop(self, *args, **kwargs) -> [bool, Union[str, Dict[str, List]]]:
        raise NotImplementedError("Subclasses should implement this method.")

    @abstractmethod
    def _copy_tmp_recipe(self, **kwargs) -> Union[str, Dict]:
        ...

    def process_recipe(self, **kwargs) -> [bool, Union[str, Dict]]:
        self.recipe = self._copy_tmp_recipe(**kwargs)
        res = True
        for i in range(self._iterations):
            self._logger.info(f"Running iteration {i + 1} of {self._iterations}:")
            res, self.recipe = self._run_loop(self.recipe, **kwargs)
            if res:
                self._logger.log(f"Expected result achieved. Stopping the iterations")
                break
        self._logger.log(f"Finished processing the recipe after {self._iterations} iterations.")
        return res, self.recipe
