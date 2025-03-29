import arabic_reshaper
import streamlit as st
from bidi import get_display


def hebrew_text(text: str, h: int = 4, color: str = "black", container=None):
    """Displays Hebrew text in Streamlit with right alignment, header style, and color.

    Args:
        text (str): The Hebrew text to display.
        h (int): Header size (1–6), similar to HTML <h1> to <h6>.
        color (str): Text color (any valid CSS color string).
    """
    if h < 1 or h > 6:
        h = 4  # fallback to h4 if out of range

    if container is None:
        st.markdown(
            f"<h{h} style='text-align: right; direction: rtl; color: {color};'>{text}</h{h}>",
            unsafe_allow_html=True
        )
    else:
        container.markdown(
            f"<h{h} style='text-align: right; direction: rtl; color: {color};'>{text}</h{h}>",
            unsafe_allow_html=True
        )


def reshape_hebrew(text):
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)
