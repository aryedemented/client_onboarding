from abc import abstractmethod
from typing import Dict, List

from scan_text_recipes.src.loop_container import LoopContainer


class PostProcessor:
    def __init__(
            self,
            config: Dict, section_name: str = None, **kwargs
    ):
        self.config = config
        self.section_name = section_name

    @abstractmethod
    def process_recipe(self, *args, **kwargs) -> Dict[str, List]:
        raise NotImplementedError("Subclasses should implement this method.")


class PostProcessorsLoopContainer(LoopContainer, PostProcessor):
    def __init__(self, iterations: int, segment_config: List[Dict], **kwargs):
        LoopContainer.__init__(
            self,
            iterations,
            package_path="scan_text_recipes.src.postprocessors",
            segment_config=segment_config,
            class_type=PostProcessor,
            **kwargs
        )
        PostProcessor.__init__(self, config={}, language=None)

    def process_recipe(self, *args, **kwargs) -> Dict[str, List]:
        raise NotImplementedError("Subclasses should implement this method.")
