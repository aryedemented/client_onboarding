import re
from typing import Union

import numpy as np
import pint.errors
from pint import UnitRegistry
from word2number import w2n


class UnitsHandler:
    def __init__(self, **kwargs):
        super().__init__()
        self.ureg = UnitRegistry()

    def get_magnitude(self, text):
        if text is None or text == "":
            return None
        if isinstance(text, str) and text.isdigit():
            return int(text)
        elif isinstance(text, str) and text.isnumeric():
            return float(text)
        try:
            return self.ureg(text).magnitude
        except (ValueError, AssertionError, AttributeError, pint.errors.UndefinedUnitError):
            pass
        try:
            return float(w2n.word_to_num(text))
        except ValueError:
            pass
        match = re.search(r'[-+]?\d*\.?\d+', text)  # Match integer or float
        return float(match.group()) if match else None

    def get_units(self, text):
        try:
            return str(self.ureg.parse_units(str(self.ureg(text).units)))
        except pint.errors.UndefinedUnitError:
            pass
        try:
            return str(self.ureg.parse_units(text.split(" ")[-1]))
        except pint.errors.UndefinedUnitError:
            pass

        try:
            return str(self.ureg.parse_units(text.split(" ")[0]))
        except pint.errors.UndefinedUnitError:
            pass

    def to(self, value: Union[str, int, float], to_unit: str) -> float:
        try:
            return self.ureg(str(value)).to(to_unit).magnitude
        except:
            pass
        try:
            val = float(value)
            return val
        except ValueError:
            pass
        return np.nan


if __name__ == '__main__':
    u_handler = UnitsHandler()
    print(u_handler.get_magnitude("2.5 kg"))
    print(u_handler.get_magnitude("2 3/4 cups"))
    print(u_handler.get_units("2.5 kg"))
    print(u_handler.to("2.5 kg", "g"))
    print(u_handler.get_magnitude("two point five kg"))
    print(u_handler.get_units("two point five kg"))
