"""Entry point for the project."""

import sys
import os
from argparse import ArgumentParser
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from evaluation_tool.compute import generate_from

def parse_arguments():
    """Parse command-line arguments."""

    parser = ArgumentParser(prog="thesis_tools")

    subparsers = parser.add_subparsers(dest="command")

    parser_generate = subparsers.add_parser(
        "generate", help="Generate outputs from given models and prompts."
    )
    parser_generate.add_argument("--models", nargs="+", type=int, required=True)
    parser_generate.add_argument("--prompts", nargs="+", type=int, required=True)

    return parser.parse_args()


def main():
    """Main entry point of the project."""

    args = parse_arguments()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, "data")
    log_path = os.path.join(data_dir, "logs")

    engine = create_engine("sqlite:///data/DB.db")
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    match args.command:
        case "generate":
            generated_path = os.path.join(data_dir, "generated")
            error = generate_from(
                args.models, args.prompts, generated_path, log_path, session
            )
            if error:
                print(
                    "at least one error occurred, consult the logs for more information"
                )
        case _:
            print("Unknown command")

    sys.exit(0)


if __name__ == "__main__":
    main()
