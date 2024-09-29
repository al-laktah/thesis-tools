"""Some utilities for evaluation tool."""

import json
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def save_to_json(output, path):
    """
    Save the outputs to specified path as JSON files.

    :param output: The data to be saved.
    :param path: path to save the data to.
    """
    try:
        with open(os.path.join(path, ".json"), "w", encoding="utf-8") as file:
            json.dump(output, file, indent=4, ensure_ascii=False)
    except TypeError as e1:
        print(e1)
        print("Error saving output as json, trying to save as file instead.")
        try:
            with open(path, "w", encoding="utf-8") as file:
                file.write(output)
        except TypeError as e2:
            print(e2)
            print("Error saving output as file, trying to save output string as file.")
            try:
                with open(path, "w", encoding="utf-8") as file:
                    file.write(str(output))
            except TypeError as e3:
                print(e3)
                print("Couldn't save output as file.")
                return False
    finally:
        print(f"Finished saving output to {path}")
    return True

def get_whitelist(vocab_dir: str):
    """Get the whitelist from the vocab directory."""
    with open(os.path.join(vocab_dir, "fp.json"), "r", encoding="utf-8") as file:
        whitelist = json.load(file)
    return whitelist


def create_directories(project_root):
    """Create directories if they do not exist."""
    data_dir = os.path.join(project_root, "data")
    directories = {
        "data": data_dir,
        "generated": os.path.join(data_dir, "generated"),
        "evaluations": os.path.join(data_dir, "evaluations"),
        "vocab": os.path.join(data_dir, "vocab"),
        "logs": os.path.join(data_dir, "logs"),
    }
    for directory in directories.values():
        os.makedirs(directory, exist_ok=True)
    return directories


def create_db_session(db_path: str):
    """Create a database session."""
    engine = create_engine(f"sqlite:///{db_path}")
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    return session
