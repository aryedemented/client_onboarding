import copy
from abc import abstractmethod
from typing import Dict, List

from scan_text_recipes.src import POST_PROCESSORS_PACKAGE_PATH, LOGGER_PACKAGE_PATH
from scan_text_recipes.src.loop_container import LoopContainer
from scan_text_recipes.utils.logger.basic_logger import BaseLogger
from scan_text_recipes.utils.utils import load_or_create_instance


class PostProcessor:
    def __init__(
            self,
            config: Dict = None, section_name: str = None, logger=None, **kwargs
    ):
        super().__init__()
        self.config = config
        self.section_name = section_name
        self.logger = load_or_create_instance(
            logger, BaseLogger, LOGGER_PACKAGE_PATH, **{**{"name": self.__class__.__name__}, **kwargs}
        )

    @abstractmethod
    def process_recipe(self, recipe_dict: Dict[str, List], recipe_text: str, **kwargs) -> [bool, Dict[str, List]]:
        raise NotImplementedError("Subclasses should implement this method.")


class PostProcessorsLoopContainer(LoopContainer, PostProcessor):
    """
    Loop container for post-processors.
    This class is responsible for managing the execution of multiple post-processors in a loop.
    It inherits from LoopContainer and PostProcessor classes.
    The class is initialized with the number of iterations
    segment_config is a list of dictionaries, each dictionary contains
    the configuration for a post-processor which are  in the loop
    """
    def __init__(self, iterations: int, segment_config: List[Dict], **kwargs):
        PostProcessor.__init__(self, **kwargs)

        LoopContainer.__init__(
            self,
            iterations,
            package_path=POST_PROCESSORS_PACKAGE_PATH,
            segment_config=segment_config,
            class_type=PostProcessor,
            logger=self.logger,
            **{key: val for key, val in kwargs.items() if key != "logger"}
        )

    def _copy_tmp_recipe(self, **kwargs) -> Dict:
        return copy.deepcopy(kwargs.get("recipe_dict"))

    def _run_loop(self, *args, **kwargs) -> [bool, Dict[str, List]]:
        recipe_dict: str = kwargs.get("recipe_dict")
        recipe_text = kwargs.get("recipe_text")
        for processor in self.processors:
            self.logger.info(f"Running {processor.__class__.__name__} post-processor")
            res, recipe_dict = processor.process_recipe(recipe_dict=recipe_dict, recipe_text=recipe_text)
            if not res:
                self.logger.error(f"Error in {processor.__class__.__name__}")
                return False, recipe_dict
        self.logger.info(f"Finished post-processing the recipe")
        return True, recipe_dict
