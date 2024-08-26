"""Module containing functions to generate and evaluate model outputs."""

from uuid import uuid4
from typing import Dict, List, Tuple, Optional
from ollama import generate, ResponseError
from pandas import DataFrame
from sqlalchemy.orm import Session

from src.db import Models, Prompts, Ris


def generate_from(
    model_id: int,
    prompt_id: int,
    session: Optional[Session] = None,
    data: Optional[DataFrame] = None,
) -> Tuple[str, List[Dict], Dict[int, Exception]]:
    """Generate outputs from given model, prompt, and data."""

    unique_id = str(uuid4())
    responses = []
    log = {}

    model = Models.get_by_id(session, model_id)
    prompt = Prompts.get_by_id(session, prompt_id)

    if data is None:
        data = Ris.get_rev_reports(session)

    for index, row in data.iterrows():
        ris_id = row["id"]
        text = row["report"]

        response = {
            "ris_id": ris_id,
            "prompt_id": prompt.id,
            "model_id": model.id,
        }

        try:
            response["raw"] = generate(
                model=model.name + ":" + model.size,
                options=model.options,
                prompt=prompt.prompt + "\n" + text,
                stream=False,
                context=None,
            )
        except ResponseError as e:
            response["raw"] = {
                "error": "An error occurred, consult the log for more information"
            }
            log[ris_id] = e
        finally:
            responses.append(response)

        if index % 25 == 0 and index != 0:
            print(f"Generated {index + 1} Outputs")

    return unique_id, responses, log
