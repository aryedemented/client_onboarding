from abc import abstractmethod, ABC
from typing import Union


class ValidationMethod(ABC):
    @staticmethod
    @abstractmethod
    def validate(value: Union[str, int, float]) -> bool:
        ...

    @staticmethod
    @abstractmethod
    def refinement_instructions(*args, **kwargs) -> str:
        raise NotImplementedError("Subclasses should implement this method.")


class NotNull(ValidationMethod):
    @staticmethod
    def validate(value: Union[str, int, float]) -> bool:
        try:
            return float(value) > 0 if value else False
        except ValueError:
            return False

    @staticmethod
    def refinement_instructions(prop, field_name, **kwargs) -> str:
        return f"The {prop} of {field_name} should not be null."


class TypeFloat(ValidationMethod):
    @staticmethod
    def validate(value: Union[str, int, float]) -> bool:
        try:
            return (isinstance(float(value), float) or value.isnumeric()) if value else False
        except ValueError:
            return False

    @staticmethod
    def refinement_instructions(prop, field_name, **kwargs) -> str:
        return f"The {prop} of {field_name} should be numeric."


class TypeInt(ValidationMethod):
    @staticmethod
    def validate(value: Union[str, int, float]) -> bool:
        try:
            return (isinstance(int(value), int) or value.isdigit()) if value else False
        except ValueError:
            return False

    @staticmethod
    def refinement_instructions(prop, field_name, **kwargs) -> str:
        return f"The {prop} of {field_name} should be integer."


class Positive(ValidationMethod):
    @staticmethod
    def validate(value: Union[str, int, float]) -> bool:
        try:
            return float(value) > 0
        except ValueError:
            return False

    @staticmethod
    def refinement_instructions(prop, field_name, **kwargs) -> str:
        return f"The {prop} of {field_name} should be postive."
