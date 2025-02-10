import pandas as pd
from langchain.tools import tool
from typing import Union
import numpy as np

EMAILS = pd.read_csv("data/raw/email_addresses.csv", header=None, names=["email_address"])


@tool("company_directory.find_email_address", return_direct=False, parse_docstring=True)
def find_email_address(name: str = "") -> Union[str, np.ndarray]:
    """
    Finds the email address of an employee by their name.

    Args:
        name: Name of the person.

    Returns
    -------
    email_address : str
        Email addresses of the person.

    Examples
    --------
    >>> directory.find_email_address("John")
    "john.smith@example.com"
    """
    global EMAILS
    if name == "":
        return "Name not provided."
    name = name.lower()
    email_address = EMAILS[EMAILS["email_address"].str.contains(name)]
    return email_address["email_address"].values
