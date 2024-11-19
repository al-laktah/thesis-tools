"""Entry point for the project."""

import sys
import os
from argparse import ArgumentParser
import language_tool_python as ltp

from evaluation_tool import general_generate
from evaluation_tool.evaluate import evaluate_from_unique_ids
from evaluation_tool.util import create_directories, create_db_session

# import nltk
from sentence_transformers import SentenceTransformer

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
    parser_evaluate.add_argument("--server", type=str)
    parser_evaluate.add_argument("--uids", nargs="+", type=str, required=True)
    parser_evaluate.add_argument("--options", nargs="+", type=int)
    parser_evaluate.add_argument("--update", action="store_true")

    return parser.parse_args()


def main():
    """Main entry point of the project."""

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    directories = create_directories(project_root)
    session = create_db_session(os.path.join(directories["data"], "DB.db"))
    model1 = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    model2 = SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')
    lang_tool = ltp.LanguageTool("de-De", remote_server="http://localhost:8010")
    #nltk.download("all")

    args = parse_arguments()

    match args.command:
        case "generate":
            general_generate(
                args.models,
                args.prompts,
                directories["generated"],
                directories["logs"],
                session,
            )
        case "evaluate":
            evaluate_from_unique_ids(
                args.uids,
                directories,
                session,
                lang_tool=lang_tool,
                model1=model1,
                model2=model2,
                options=args.options,
                update=args.update,
            )
            if lang_tool:
                lang_tool.close()
        case _:
            print("Unknown command")

    session.close()
    lang_tool.close()
    sys.exit(0)


if __name__ == "__main__":
    main()
