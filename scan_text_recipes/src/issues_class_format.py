from dataclasses import dataclass


@dataclass
class Issue:
    problem: str
    solution: str


@dataclass
class SupplementaryPromptQuestion:
    format: str
    section: str
    field_name: str
    section_index: int
    units: str

    @property
    def question(self) -> str:
        return f'What is the {self.field_name} for {self.section} in the recipe in {self.units}?'

    @property
    def format_text(self) -> str:
        return f'{{ "name": "{self.section}", "value": "NUMERIC VALUE ONLY" , "units": "{self.units}"}}'

    @property
    def problem(self) -> str:
        return f'Failed to get {self.field_name} for {self.section} in the recipe in "{self.units}".'
