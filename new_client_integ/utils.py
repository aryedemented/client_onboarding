import os
import re
from typing import Dict, Any, Tuple
import pandas as pd
from functools import lru_cache
import difflib

# Determine if cache should be used (e.g., skip caching in AWS Lambda)
USE_CACHE = os.getenv('USE_CACHE', '1') == '1'


def highlight_differences(a: str, b: str) -> Tuple[str, str]:
    seq = difflib.SequenceMatcher(None, a, b)
    a_out = ""
    b_out = ""

    for tag, i1, i2, j1, j2 in seq.get_opcodes():
        if tag == "equal":
            a_out += a[i1:i2]
            b_out += b[j1:j2]
        else:
            a_out += f"<span style='color:red'>{a[i1:i2]}</span>"
            b_out += f"<span style='color:red'>{b[j1:j2]}</span>"

    # Frame with styled div (simulates a textbox)
    box_style = (
        "border:1px solid #ccc; padding:10px; margin:5px 0; "
        "border-radius:5px; background-color:#f9f9f9; "
        f"direction: rtl; font-size: 18px; font-family: monospace;"
    )
    a_out = f"<div style='{box_style}'>{a_out}</div>"
    b_out = f"<div style='{box_style}'>{b_out}</div>"

    return a_out, b_out


def conditional_cache(maxsize=128):
    """Decorator that applies lru_cache only if USE_CACHE is enabled."""
    def decorator(func):
        if USE_CACHE:
            return lru_cache(maxsize=maxsize)(func)
        else:
            return func
    return decorator


def clean_text(text: str) -> str:
    # Step 1: Keep Hebrew, English, ", ', -, ,, ., and spaces
    text = re.sub(r"[^a-zA-Zא-ת\"'\-., ]", "", text)
    # Step 2: Collapse multiple spaces into a single space
    text = re.sub(r"\s+", " ", text)
    # Step 3: Strip leading/trailing spaces
    return text.strip()


def select_rows_by_dict(df, selection: Dict[str, Any]) -> pd.DataFrame:
    """
    Select rows from a DataFrame based on column-value pairs.

    Args:
        df (pd.DataFrame): The DataFrame to filter.
        selection (dict): Dictionary where keys are column names and values are the required values.

    Returns:
        pd.DataFrame: Filtered DataFrame.
    """
    mask = pd.Series(True, index=df.index)
    for col, val in selection.items():
        if col in df.columns:
            mask &= (df[col] == val)
    return df[mask]
