import random
import string

import pandas as pd


def generate_random_string(n: int = 10) -> str:
    """
    generates random string

    Args:
        n: random string's length

    Returns:
        random string
    """
    return "".join(  # nosec B311
        random.choices(string.ascii_uppercase + string.digits, k=n)  # nosec B311
    )  # nosec B311


def dataframe_as_list_of_dict(df: pd.DataFrame) -> list[dict[str, float]]:
    """
    converts dataframe to list of dictionaries

    Args:
        df: target dataframe to convert

    Returns:
        list of dictionaries, which is generated by given dataframe
    """
    ret = []
    keys = list(df.columns)
    for val in df.values:
        ret.append(dict(zip(keys, val)))
    return ret
