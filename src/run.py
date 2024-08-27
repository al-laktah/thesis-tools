"""Entry point for the project."""

import sys
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

    engine = create_engine("sqlite:///data/DB.db")
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    match args.command:
        case "generate":
            generate_from(args.models, args.prompts, session)
        case _:
            print("Unknown command")

    sys.exit(0)


if __name__ == "__main__":
    main()
