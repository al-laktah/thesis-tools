"""Some utilities for evaluation tool."""

import json

def save_to_json(output, path):
    """
    Save the outputs to specified path as JSON files.

    :param output: The data to be saved.
    :param path: path to save the data to.
    """
    with open(
        path, "w", encoding="utf-8"
    ) as file:
        json.dump(output, file, indent=4, ensure_ascii=False)
