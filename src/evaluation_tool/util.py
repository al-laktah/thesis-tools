"""Some utilities for evaluation tool."""

import json

def save_to_json(output, path):
    """
    Save the outputs to specified log and generated paths as JSON files.

    :param output: The data to be saved.
    :param path: path to save the data.
    """
    with open(
        path, "w", encoding="utf-8"
    ) as file:
        json.dump(output, file, indent=4, ensure_ascii=False)
