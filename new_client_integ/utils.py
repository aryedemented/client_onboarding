import os
import re
from typing import Dict, Any
import pandas as pd
from functools import lru_cache

# Determine if cache should be used (e.g., skip caching in AWS Lambda)
USE_CACHE = os.getenv('USE_CACHE', '1') == '1'


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
