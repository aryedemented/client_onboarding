class BasePage:
    def __init__(self):
        self.title = "Base Page"

    def render(self):
        raise NotImplementedError("Subclasses should implement this!")
