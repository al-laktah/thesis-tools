"""Entry point for the project."""

import sys
import os
import json
from argparse import ArgumentParser
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import language_tool_python as ltp

from evaluation_tool.compute import generate_from
from evaluation_tool.evaluate import evaluate_from_unique_id


def parse_arguments():
    """Parse command-line arguments."""

    parser = ArgumentParser(prog="thesis_tools")

    subparsers = parser.add_subparsers(dest="command")

    parser_generate = subparsers.add_parser(
        "generate", help="Generate outputs from given models and prompts."
    )
    parser_generate.add_argument("--models", nargs="+", type=int, required=True)
    parser_generate.add_argument("--prompts", nargs="+", type=int, required=True)

    parser_evaluate = subparsers.add_parser("evaluate", help="evaluate outputs.")
    parser_evaluate.add_argument("--server", type=str, required=True)
    parser_evaluate.add_argument("--uid", type=str, required=True)

    return parser.parse_args()


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


def get_whitelist(vocab_dir: str):
    """Get the whitelist from the vocab directory."""
    with open(os.path.join(vocab_dir, "fp.json"), "r", encoding="utf-8") as file:
        whitelist = json.load(file)
    return whitelist


def main():
    """Main entry point of the project."""

    args = parse_arguments()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    directories = create_directories(project_root)

    db_path = os.path.join(directories["data"], "DB.db")
    engine = create_engine(f"sqlite:///{db_path}")
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    match args.command:
        case "generate":
            generate_from(
                args.models,
                args.prompts,
                directories["generated"],
                directories["logs"],
                session,
            )
        case "evaluate":
            evaluate_from_unique_id(
                args.uid,
                directories["generated"],
                directories["evaluations"],
                session,
                ltp.LanguageTool("de-De", remote_server=args.server),
                whitelist=get_whitelist(directories["vocab"]),
                save_json=True,
            )
        case _:
            print("Unknown command")

    sys.exit(0)


if __name__ == "__main__":
    main()
