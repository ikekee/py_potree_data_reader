"""This module contains functions for working with files."""
import json
from pathlib import Path
from typing import Any
from typing import Dict


def open_json(file_path: Path) -> Dict[Any, Any]:
    """Open a json file and return the data.

    Args:
        file_path: A path to the file for reading.

    Returns:
        JSON data as python dictionary.
    """
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data


def create_path_if_not_exists(path: Path) -> None:
    """Creates a path (folders and subfolders) if it doesn't exist.

    Args:
        path: A path to the folder.
    """
    if not path.exists():
        path.mkdir(parents=True)
