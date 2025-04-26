from typing import Dict, Any

import pandas as pd


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
