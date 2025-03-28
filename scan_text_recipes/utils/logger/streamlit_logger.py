from typing import List

from scan_text_recipes.utils.logger.basic_logger import BaseLogger


class StreamlitLogger(BaseLogger):
    def __init__(
            self, name: str, session_state, log_area, log_lines: List[str], fixed_size_window: bool = True, **kwargs
    ):
        super().__init__(name, **kwargs)
        self.session_state = session_state
        self.log_area = log_area
        self.log_lines = log_lines
        self.fixed_size_window = fixed_size_window

    def log(self, message: str):
        self.fetch_msg(message, color="gray")

    def info(self, message: str):
        self.fetch_msg(message, color="green")

    def warning(self, message: str):
        self.fetch_msg(message, color="orange")

    def error(self, message: str):
        self.fetch_msg(message, color="red")

    def critical(self, message: str):
        self.fetch_msg(message, color="red")

    @property
    def fixed_size_window_header(self, color: str = "#f9ebea", size: str = "300px") -> str:
        return f"""
        <div style="
            height: {size};
            overflow-y: auto;
            background-color: { color};
            color: white;
            padding: 10px;
            border-radius: 8px;
            font-family: monospace;
            font-size: 14px;
            border: 1px solid #444;
            margin: 0;
        ">
        """

    def fetch_msg(self, msg: str, color="gray"):
        self.log_lines.append((msg, color))
        # Re-render
        html = "<div style='font-family: monospace; white-space: pre;'>"
        for line, col in self.log_lines:
            html += f"<span style='color:{col};'>{line}</span><br>"
        html += "</div>"
        if self.fixed_size_window:
            html = self.fixed_size_window_header + html + "</div>"
        self.log_area.markdown(html, unsafe_allow_html=True)
